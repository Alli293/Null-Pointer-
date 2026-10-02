"""Sensores a bordo: ultrasonico HCSR04 e infrarrojo (pines de fabrica).

Producen las señales `tiene_cubo` / `cubo_entregado` de RoverFSM.transicion():
la vision da posicion, no contacto fisico (ver docs/arquitectura.md).
"""

import board
from hcsr04 import HCSR04
from firmware import config, placa


class Sensores:
    def __init__(self):
        self._sonar = HCSR04(
            getattr(board, config.PIN_ULTRASONICO_TRIG),
            getattr(board, config.PIN_ULTRASONICO_ECHO),
        )
        self._ir = placa.ideaboard().DigitalIn(getattr(board, config.PIN_IR))
        self._tenia_cubo = False

    def leer_infrarrojo(self):
        return self._ir.value

    def leer_distancia_ultrasonico_cm(self):
        """Distancia en cm, o None si la lectura falla / no hay eco."""
        try:
            d = self._sonar.dist_cm()
        except Exception:
            return None
        return d if d and d > 0 else None

    def cubo_sujeto(self):
        """True si el cubo esta dentro de las paletas (ultrasonico cercano).

        TODO: reforzar con sensor de color/switch si el kit lo trae; hoy es
        solo una heuristica de distancia.
        """
        d = self.leer_distancia_ultrasonico_cm()
        sujeto = d is not None and d <= config.DISTANCIA_AGARRE_CM
        self._tenia_cubo = sujeto
        return sujeto

    def cubo_liberado_en_depot(self):
        """True cuando el cubo deja de detectarse tras haberlo tenido."""
        d = self.leer_distancia_ultrasonico_cm()
        suelto = d is None or d > config.DISTANCIA_AGARRE_CM
        return self._tenia_cubo and suelto
