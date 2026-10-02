"""Una sola IdeaBoard compartida por todo el firmware.

IdeaBoard() reserva los pines PWM de los motores (IO12-IO15) y el NeoPixel; crear una
segunda instancia falla con "pin in use". Motores, sensores e indicador LED deben
pedirla siempre por aqui.
"""

_ib = None


def ideaboard():
    global _ib
    if _ib is None:
        from ideaboard import IdeaBoard

        _ib = IdeaBoard()
    return _ib
