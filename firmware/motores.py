"""Primitivas de motor. Adaptar de codigos/test_motores.py y
codigos/motor_calibration.py (repo guia) una vez confirmados los pines y el
driver de motor del kit -- por ahora son stubs para poder importar y probar el
resto del firmware sin hardware conectado.

TODO: factor de calibracion por motor (motor_calibration.py del repo guia
compensa que un motor suele girar mas rapido que el otro).
"""

from firmware import config


class Motores:
    def __init__(self):
        # TODO: inicializar PWM/GPIO reales con machine.Pin / machine.PWM sobre
        # config.PIN_MOTOR_*.
        self._factor_calibracion_izq = 1.0
        self._factor_calibracion_der = 1.0

    def avanzar(self, velocidad=1.0):
        # TODO: aplicar velocidad * factor_calibracion a cada motor.
        pass

    def retroceder(self, velocidad=1.0):
        pass

    def girar_en_sitio(self, velocidad=1.0, sentido_horario=True):
        pass

    def detener(self):
        # Debe poder llamarse en cualquier momento (incluye phase == FINISHED),
        # asi que no debe depender de ningun otro estado interno.
        pass
