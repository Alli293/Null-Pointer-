"""Primitivas de motor sobre la libreria ideaboard (CircuitPython).

throttle va de -1.0 a 1.0; 0.0 frena; None deja rodar libre.
"""

from firmware import config, placa


class Motores:
    def __init__(self):
        self._ib = placa.ideaboard()
        self._izq = getattr(self._ib, "motor_%d" % config.MOTOR_IZQ)
        self._der = getattr(self._ib, "motor_%d" % config.MOTOR_DER)
        # TODO: calibrar (un motor suele girar mas rapido que el otro).
        self._factor_izq = 1.0
        self._factor_der = 1.0

    def _aplicar(self, izq, der):
        if config.INVERTIR_IZQ:
            izq = -izq
        if config.INVERTIR_DER:
            der = -der
        self._izq.throttle = max(-1.0, min(1.0, izq * self._factor_izq))
        self._der.throttle = max(-1.0, min(1.0, der * self._factor_der))

    def mover(self, izq, der):
        """Comando directo de ruedas, cada una en [-1, 1] (lo que entrega
        comun.rover.ControladorRover.paso)."""
        self._aplicar(izq, der)

    def avanzar(self, velocidad=1.0):
        self._aplicar(velocidad, velocidad)

    def retroceder(self, velocidad=1.0):
        self._aplicar(-velocidad, -velocidad)

    def girar_en_sitio(self, velocidad=1.0, sentido_horario=True):
        s = 1.0 if sentido_horario else -1.0
        self._aplicar(velocidad * s, -velocidad * s)

    def detener(self):
        # Seguro de llamar en cualquier momento (incluye phase == FINISHED).
        self._izq.throttle = 0.0
        self._der.throttle = 0.0
