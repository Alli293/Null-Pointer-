"""Wrappers de los sensores a bordo del rover, sobre CircuitPython.

IR, ultrasonico e IMU usan pines/direccion confirmados en banco de pruebas
(ver firmware/config.py y firmware/README.md).

Sensor de luz/color (modulo VCC/DI/AO/GND, ver conexiones/sensorcolor2.png del
repo guia): en banco se confirmo que el NeoPixel (DI) y el fototransistor (AO)
reaccionan fuerte a cualquier objeto reflectante muy cerca, pero **no** se pudo
lograr que distinga rojo de verde de forma confiable (los dos dan lecturas
casi identicas con este sensor simple, sin filtro de color real). Por diseño,
tampoco hace falta: `comun/maquina_estados.py` solo necesita saber si el rover
tiene ALGO agarrado (`tiene_cubo`), no de que color -- el color del cubo que se
persigue ya se conoce por `color_asignado` (viene de la vision externa, ver
docs/arquitectura.md). Por eso `cubo_sujeto()` mide presencia (¿cambia mucho la
luz reflejada cuando prendo el LED?), no color.

TODO (mejora opcional, no bloqueante): si mas adelante quieren una confirmacion
redundante del COLOR agarrado (no solo presencia), en banco se vio un patron
usable -- ROJO/VERDE promediados se oscurecen mucho respecto a apagado si el
cubo es rojo, se aclaran mucho si es verde, y casi no cambian si es azul. Pero
esto necesita una distancia fija (guia fisica) para calibrar umbrales en serio.
"""

import time

import board
import analogio
import neopixel

from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC

try:
    from hcsr04 import HCSR04
except ImportError:  # pragma: no cover - falta copiar la lib al robot todavia
    HCSR04 = None

from firmware import config

# Cuanto tiene que cambiar la lectura de luz (encendido vs apagado) para
# considerar que hay un cubo pegado al sensor. Punto de partida de banco (ver
# firmware/README.md): con cualquier cubo a distancia de agarre, el cambio
# observado fue de >1500 sobre una escala de 16 bits -- este umbral se queda
# comodo por debajo de eso. Ajustar con banco real (comparar "nada enfrente"
# contra "cubo agarrado") antes de la ronda.
UMBRAL_DESVIACION_CUBO = 800


class Sensores:
    def __init__(self):
        self._ir = tuple(
            analogio.AnalogIn(getattr(board, pin))
            for pin in (
                config.PIN_IR_ADELANTE_IZQ,
                config.PIN_IR_ADELANTE_DER,
                config.PIN_IR_ATRAS_IZQ,
                config.PIN_IR_ATRAS_DER,
            )
        )

        self._sonar = None
        if HCSR04 is not None:
            self._sonar = HCSR04(
                getattr(board, config.PIN_ULTRASONICO_TRIG),
                getattr(board, config.PIN_ULTRASONICO_ECHO),
            )

        i2c = board.I2C()
        self._imu = LSM6DS3TRC(i2c, config.IMU_I2C_ADDR)

        self._pixel_color = None
        self._luz = None
        if config.PIN_NEOPIXEL_COLOR is not None and config.PIN_SENSOR_LUZ is not None:
            self._pixel_color = neopixel.NeoPixel(
                getattr(board, config.PIN_NEOPIXEL_COLOR), 1, brightness=1, auto_write=True
            )
            self._luz = analogio.AnalogIn(getattr(board, config.PIN_SENSOR_LUZ))

    def leer_infrarrojos(self):
        """4 lecturas analogicas crudas [0, 65535] de los sensores IR."""
        return tuple(s.value for s in self._ir)

    def leer_distancia_ultrasonico_cm(self):
        if self._sonar is None:
            return None
        try:
            return self._sonar.dist_cm()
        except RuntimeError:
            # HCSR04 lanza RuntimeError si no hay eco (nada dentro de rango) --
            # no es un fallo real, solo "no hay nada cerca".
            return None

    def _medir_luz(self, color, muestras=10):
        self._pixel_color[0] = color
        time.sleep(0.05)
        total = 0
        for _ in range(muestras):
            total += self._luz.value
            time.sleep(0.005)
        return total / muestras

    def leer_orientacion_imu(self):
        """(aceleracion_xyz, giro_xyz) del LSM6DS3TRC, para correccion fina."""
        return self._imu.acceleration, self._imu.gyro

    def cubo_sujeto(self):
        """True si algo muy reflectante (un cubo) esta pegado al sensor.

        No identifica color -- ver nota de modulo. Usado como `tiene_cubo` en
        RoverFSM.transicion().
        """
        if self._pixel_color is None:
            return False  # sensor de color no disponible en este robot/config
        apagado = self._medir_luz((0, 0, 0))
        encendido = self._medir_luz((255, 255, 255))
        self._pixel_color[0] = (0, 0, 0)
        return abs(encendido - apagado) > UMBRAL_DESVIACION_CUBO

    def cubo_liberado_en_depot(self):
        """True si se confirmo la entrega por sensor propio (redundante a la
        confirmacion por vision -- ver docs/contrato_telemetria.md).

        Usado como `cubo_entregado` en RoverFSM.transicion().
        """
        return False  # TODO
