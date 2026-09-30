"""Indicador de estado con el NeoPixel del rover (IO33, orden GRB).

Sin cable USB no hay REPL ni `print`: el LED dice que esta haciendo el rover.
Tabla en el README raiz (seccion "Indicador LED"). Nunca debe romper el firmware: si
el LED falla, simplemente no se muestra nada.

Paleta pensada para el LED de estos rovers, donde el rojo MEZCLADO con otros canales
se pierde (se vio rojo puro, pero no amarillo/magenta/rosa): solo se usan verde, azul,
cian, blanco y rojo puro. Cada familia de color dice una cosa y el parpadeo dice la etapa:
  azul  = conexion      verde = trabajando     cian = buscar/entregar
  blanco = terminado    rojo  = problema

Ojo: NO se usa `board.NEOPIXEL` (IO2) de la IdeaBoard: en estos rovers no muestra nada;
el LED que responde esta en IO33 (ver config.PIN_LED).
"""

import time

import board
import neopixel

from firmware import config

BRILLO = 0.5

FIJO = "fijo"
LENTO = "lento"     # 1 Hz: 0.5 s encendido, 0.5 s apagado
RAPIDO = "rapido"   # 4 Hz: 0.125 s encendido, 0.125 s apagado

AZUL = (0, 0, 255)
VERDE = (0, 255, 0)
CIAN = (0, 255, 255)
BLANCO = (255, 255, 255)
ROJO = (255, 0, 0)

# clave -> (color, patron)
COLORES = {
    # Arranque y red
    "conectando": (AZUL, RAPIDO),       # conectando al WiFi / a la vision
    "esperando": (AZUL, FIJO),          # conectado; la ronda aun no esta en RUNNING (no se mueve)
    "sin_telemetria": (ROJO, LENTO),    # dejo de llegar telemetria: motores frenados
    "error": (ROJO, FIJO),              # error (p. ej. falta VISION_HOST): motores frenados
    # Estados del FSM (comun/maquina_estados.py)
    "APROXIMAR": (VERDE, LENTO),        # yendo a ubicarse detras del cubo
    "SUJETAR": (VERDE, RAPIDO),         # empujando hasta confirmar que lleva el cubo
    "TRANSPORTAR": (VERDE, FIJO),       # empujando el cubo al depot
    "ENTREGAR": (CIAN, FIJO),           # solto el cubo, retrocede
    "BUSCAR": (CIAN, LENTO),            # sin cubo fresco que atender
    "OCIOSO": (BLANCO, FIJO),           # termino su cola de colores
    "DETENIDO": (BLANCO, LENTO),        # ronda terminada (FINISHED)
}

_APAGADO = (0, 0, 0)


def _encendido(patron, t):
    """True si el LED debe estar encendido `t` segundos despues de empezar el patron."""
    if patron == LENTO:
        return (t % 1.0) < 0.5
    if patron == RAPIDO:
        return (t % 0.25) < 0.125
    return True


class Indicador:
    def __init__(self, reloj=None):
        self._reloj = reloj or time.monotonic
        self._clave = None
        self._t0 = 0.0
        self._escrito = None
        try:
            self._np = neopixel.NeoPixel(
                getattr(board, config.PIN_LED), 1, brightness=BRILLO, auto_write=True
            )
            self._np[0] = _APAGADO
            self._escrito = _APAGADO
        except Exception:
            self._np = None

    def mostrar(self, clave):
        """Cambia el estado que se muestra. Al cambiar empieza encendido."""
        if clave == self._clave:
            return
        self._clave = clave
        self._t0 = self._reloj()
        self.actualizar()

    def actualizar(self):
        """Aplica el parpadeo. Llamar seguido (una vez por vuelta del loop principal)."""
        if self._np is None or self._clave is None:
            return
        color, patron = COLORES.get(self._clave, (_APAGADO, FIJO))
        deseado = color if _encendido(patron, self._reloj() - self._t0) else _APAGADO
        if deseado == self._escrito:
            return
        try:
            self._np[0] = deseado
            self._escrito = deseado
        except Exception:
            pass
