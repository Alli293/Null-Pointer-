"""Helpers para leer el mundo (mensaje de telemetria) por identidad, nunca por
posicion en la lista (Regla 1 del contrato).

Portable CPython <-> MicroPython: solo dict/list/math basico, sin dependencias
externas.
"""

from comun import contrato

try:
    from math import sqrt
except ImportError:  # pragma: no cover - MicroPython siempre trae math
    def sqrt(x):
        return x ** 0.5


def mi_rover(msg, mi_id):
    """Devuelve el dict del rover propio segun su id de marcador ArUco, o None."""
    for r in msg.get("rovers", ()):
        if r.get("id") == mi_id:
            return r
    return None


def cubo_por_color(msg, color):
    """Devuelve el dict del cubo de ese color, o None si no esta en el mensaje."""
    for c in msg.get("cubes", ()):
        if c.get("color") == color:
            return c
    return None


def depot_por_color(msg, color):
    """Devuelve el depot (zona de entrega) de ese color, o None."""
    for d in msg.get("depots", ()):
        if d.get("color") == color:
            return d
    return None


def clasificar_frescura(age_ms):
    """Clasifica un age_ms en FRESCO / DUDOSO / NO_CONFIABLE (Regla 2)."""
    if age_ms is None:
        return contrato.NO_CONFIABLE
    if age_ms < contrato.UMBRAL_FRESCO_MS:
        return contrato.FRESCO
    if age_ms < contrato.UMBRAL_DUDOSO_MS:
        return contrato.DUDOSO
    return contrato.NO_CONFIABLE


def es_fresco(objeto):
    """True si un rover/cubo/depot (con campo age_ms) es utilizable ahora mismo.

    depots y start no traen age_ms (son estaticos) -- se consideran siempre frescos.
    """
    if objeto is None:
        return False
    if "age_ms" not in objeto:
        return True
    return clasificar_frescura(objeto["age_ms"]) == contrato.FRESCO


def distancia(a, b):
    """Distancia euclidiana en celdas entre dos objetos con campos col/row."""
    dcol = a["col"] - b["col"]
    drow = a["row"] - b["row"]
    return sqrt(dcol * dcol + drow * drow)


def cubo_en_su_zona(cubo, depot, depot_size, grid, cube_side):
    """Verificacion EXACTA de entrega (protocolo v2): el cubo entero adentro de
    su zona rectangular, con cualquier rotacion. Devuelve (adentro, cuanto_falta).

    Adaptada tal cual del contrato (CONTRATO.md, seccion "Cuando un cubo esta en
    su zona"), que la da lista para copiar porque es la misma cuenta que usa el
    sistema de visión para decidir el veredicto oficial -- no conviene
    reinventarla con un umbral de distancia al centro.
    """
    distancias = {
        "arriba": depot["row"],
        "abajo": grid["rows"] - depot["row"],
        "izquierda": depot["col"],
        "derecha": grid["cols"] - depot["col"],
    }
    lado = min(distancias, key=lambda l: distancias[l])

    if lado in ("arriba", "abajo"):
        semi_col, semi_row = depot_size["length"] / 2, depot_size["depth"] / 2
    else:
        semi_col, semi_row = depot_size["depth"] / 2, depot_size["length"] / 2

    margen = cube_side * sqrt(2) / 2

    exceso_col = max(0.0, abs(cubo["col"] - depot["col"]) - (semi_col - margen))
    exceso_row = max(0.0, abs(cubo["row"] - depot["row"]) - (semi_row - margen))
    falta = sqrt(exceso_col * exceso_col + exceso_row * exceso_row)
    return falta == 0.0, falta


def tiempo_restante_ms(msg):
    """Milisegundos que quedan de la fase actual segun el reloj OFICIAL del
    mensaje (`clock.remaining_ms`), o None si el mensaje no trae `clock`
    (mensajes viejos/otra version). No llevar un cronometro propio -- el del
    rover se desincroniza del oficial (Regla 6.4 / seccion "clock" del contrato)."""
    clock = msg.get("clock")
    return clock.get("remaining_ms") if clock else None


class EstimadorLatencia:
    """Mide cuanto ha crecido el retraso de los mensajes respecto a la primera
    muestra recibida, en vez de una latencia absoluta.

    El contrato no garantiza reloj sincronizado entre la PC de vision y el rover
    (ver docs/contrato_telemetria.md), asi que `ahora_ms - ts_ms` en la primera
    muestra puede ser cualquier numero -- lo tratamos como el "offset base" y solo
    nos importa si ese offset empieza a crecer (seria una senal real de latencia/
    cola, no de desfase de reloj).
    """

    def __init__(self):
        self._offset_base = None

    def reset(self):
        self._offset_base = None

    def actualizar(self, msg, ahora_ms):
        """Devuelve la variacion de latencia en ms (>= 0) desde la primera muestra."""
        offset_actual = ahora_ms - msg["ts_ms"]
        if self._offset_base is None:
            self._offset_base = offset_actual
            return 0
        variacion = offset_actual - self._offset_base
        return variacion if variacion > 0 else 0


def mensaje_utilizable(msg, ahora_ms, estimador_latencia):
    """Chequeo combinado antes de tomar cualquier decision de movimiento:
    version soportada, fase que permite actuar, y latencia bajo control.

    No valida frescura de objetos individuales -- eso se hace por objeto con
    clasificar_frescura()/es_fresco(), porque un cubo ocluido no invalida el resto
    del mensaje.
    """
    if not contrato.validar_version(msg):
        return False
    if msg.get("phase") not in (contrato.FASE_READY, contrato.FASE_RUNNING):
        return False
    variacion = estimador_latencia.actualizar(msg, ahora_ms)
    return variacion < contrato.UMBRAL_VARIACION_LATENCIA_MS
