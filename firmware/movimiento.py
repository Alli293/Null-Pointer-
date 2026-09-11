"""Traduce "hacia donde ir" (un objetivo con col/row) en comandos de motor.

Adaptar de codigos/move_heading.py, codigos/turn_angle.py y codigos/code_PID.py
(repo guia) para el control fino de rumbo -- aca va solo el esqueleto de la
interfaz que usa main.py.
"""

try:
    from math import atan2, degrees, pi
except ImportError:  # pragma: no cover
    atan2 = degrees = pi = None

from firmware.motores import Motores


def rumbo_hacia(rover, objetivo):
    """Angulo en grados [0, 360) desde `rover` hacia `objetivo`, en el mismo
    sistema que `theta` en la telemetria (0 = derecha, antihorario)."""
    dcol = objetivo["col"] - rover["col"]
    drow = rover["row"] - objetivo["row"]  # row crece hacia abajo -> invertir
    angulo = degrees(atan2(drow, dcol))
    return angulo % 360


class ControladorMovimiento:
    """Envuelve Motores() con la logica de "avanzar hacia" / "girar hasta".

    TODO: PID real sobre el error de rumbo (code_PID.py) en vez de bang-bang;
    esto es solo el esqueleto de la interfaz para que main.py ya pueda llamarlo.
    """

    def __init__(self):
        self.motores = Motores()

    def avanzar_hacia(self, rover, objetivo):
        objetivo_theta = rumbo_hacia(rover, objetivo)
        error = (objetivo_theta - rover["theta"] + 180) % 360 - 180
        # TODO: reemplazar por PID; por ahora, corregir rumbo si el error es
        # grande, si no avanzar derecho.
        if abs(error) > 15:
            self.motores.girar_en_sitio(sentido_horario=error < 0)
        else:
            self.motores.avanzar()

    def detener(self):
        self.motores.detener()
