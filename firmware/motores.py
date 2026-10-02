"""Primitivas de motor sobre el driver de la IdeaBoard (CircuitPython).

Usa ib.motor_1 / ib.motor_2 de la libreria ideaboard.py del kit (throttle en
[-1.0, 1.0], 0.0 = detenido) -- confirmado en banco que ambos motores giran en
las dos direcciones con el jumper SELECT-Vin puesto (ver firmware/README.md).

TODO: factor de calibracion por motor (motor_calibration.py del repo guia
compensa que un motor suele girar mas rapido que el otro).
"""

from ideaboard import IdeaBoard

from firmware import config


class Motores:
    def __init__(self):
        self._ib = IdeaBoard()
        self._factor_izq = 1.0
        self._factor_der = 1.0

    def _throttle(self, izq, der):
        motor_izq = self._ib.motor_1 if config.MOTOR_1_ES_IZQUIERDO else self._ib.motor_2
        motor_der = self._ib.motor_2 if config.MOTOR_1_ES_IZQUIERDO else self._ib.motor_1
        motor_izq.throttle = max(-1.0, min(1.0, izq * self._factor_izq))
        motor_der.throttle = max(-1.0, min(1.0, der * self._factor_der))

    def avanzar(self, velocidad=1.0):
        self._throttle(velocidad, velocidad)

    def retroceder(self, velocidad=1.0):
        self._throttle(-velocidad, -velocidad)

    def girar_en_sitio(self, velocidad=1.0, sentido_horario=True):
        signo = 1 if sentido_horario else -1
        self._throttle(signo * velocidad, -signo * velocidad)

    def detener(self):
        # Debe poder llamarse en cualquier momento (incluye phase == FINISHED),
        # asi que no debe depender de ningun otro estado interno.
        self._ib.motor_1.throttle = 0.0
        self._ib.motor_2.throttle = 0.0
