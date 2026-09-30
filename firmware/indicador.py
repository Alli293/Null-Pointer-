"""Indicador de estado con el LED RGB (NeoPixel) de la IdeaBoard.

Sin cable USB no hay REPL ni `print`: el color del LED dice que esta haciendo el rover.
Tabla de colores en el README raiz (seccion "Indicador LED"). Nunca debe romper el
firmware: si el LED falla, simplemente no se muestra nada.
"""

from firmware import placa

BRILLO = 0.3

COLORES = {
    # Arranque y red
    "conectando": (255, 180, 0),       # amarillo: conectando al WiFi / a la vision
    "esperando": (0, 0, 80),           # azul tenue: conectado, la ronda aun no esta en RUNNING
    "sin_telemetria": (255, 60, 0),    # naranja: dejo de llegar telemetria (motores frenados)
    "error": (255, 0, 0),              # rojo: error (p. ej. falta VISION_HOST); motores frenados
    # Estados del FSM (comun/maquina_estados.py)
    "BUSCAR": (120, 0, 255),           # violeta
    "APROXIMAR": (0, 0, 255),          # azul
    "SUJETAR": (255, 0, 255),          # magenta
    "TRANSPORTAR": (0, 255, 0),        # verde
    "ENTREGAR": (0, 255, 255),         # cian
    "OCIOSO": (255, 255, 255),         # blanco: termino su cola de colores
    "DETENIDO": (255, 80, 120),        # rosa: ronda terminada (FINISHED)
}


class Indicador:
    def __init__(self):
        self._ultimo = None
        try:
            self._ib = placa.ideaboard()
            self._ib.brightness = BRILLO
        except Exception:
            self._ib = None

    def mostrar(self, clave):
        """Pone el color de `clave`; solo escribe si cambio."""
        if self._ib is None or clave == self._ultimo:
            return
        self._ultimo = clave
        try:
            self._ib.pixel = COLORES.get(clave, (0, 0, 0))
        except Exception:
            pass
