"""Wrappers de los sensores a bordo del rover: IR, ultrasonico, color, IMU.

Adaptar de codigos/code_4IR.py, code_ultrasonic.py, color_detect.py y
code_acc.py (repo guia) una vez confirmados los pines -- stubs por ahora.

Estas lecturas son las que producen las señales `tiene_cubo` / `cubo_entregado`
que main.py le pasa a RoverFSM.transicion(): la vision da posicion, no
contacto fisico (ver docs/arquitectura.md).
"""

from firmware import config


class Sensores:
    def __init__(self):
        pass  # TODO: inicializar Pin/ADC/I2C reales sobre config.PIN_*

    def leer_infrarrojos(self):
        """4 lecturas booleanas/analogas de los sensores IR (linea/borde)."""
        return (False, False, False, False)  # TODO

    def leer_distancia_ultrasonico_cm(self):
        return None  # TODO

    def leer_color(self):
        """Color detectado muy cerca del sensor (para confirmar agarre), o None."""
        return None  # TODO

    def leer_orientacion_imu(self):
        """Lectura de acelerometro/giroscopio para correccion fina (code_acc.py)."""
        return None  # TODO

    def cubo_sujeto(self):
        """True si el sensor de color/switch confirma que el cubo esta agarrado.

        Usado como `tiene_cubo` en RoverFSM.transicion().
        """
        return self.leer_color() is not None  # TODO: heuristica real

    def cubo_liberado_en_depot(self):
        """True si se confirmo la entrega (p.ej. el sensor de color deja de ver
        el cubo justo despues de la maniobra de soltar).

        Usado como `cubo_entregado` en RoverFSM.transicion().
        """
        return False  # TODO
