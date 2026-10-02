"""Loop principal del rover (CircuitPython): conectar, leer telemetria,
decidir, actuar.

Estado actual: WiFi hacia el sistema de vision y ESP-NOW entre los dos rovers
quedaron verificados en banco de pruebas (ver docs/arquitectura.md). Lo que
sigue pendiente de banco es la geometria fina de acercamiento/agarre
(firmware/movimiento.py) y el sensor de color (firmware/sensores.py).
"""

from firmware import config
from firmware.comm_vision import ClienteVision
from firmware.comm_espnow import ComunicacionRovers
from firmware.movimiento import ControladorMovimiento
from firmware.sensores import Sensores

from comun import contrato, mundo
from comun.maquina_estados import (
    RoverFSM,
    ESTADO_APROXIMAR,
    ESTADO_TRANSPORTAR,
    ESTADO_SUJETAR,
    ESTADO_ENTREGAR,
    ESTADO_DETENIDO,
)


def conectar_wifi():
    import wifi
    wifi.radio.connect(config.WIFI_SSID, config.WIFI_PASSWORD)


def ahora_ms():
    # time.monotonic() es un contador monotonico en segundos (no epoca) en
    # CircuitPython -- exactamente lo que necesita EstimadorLatencia (solo le
    # importa la diferencia entre muestras, no el valor absoluto).
    import time
    return int(time.monotonic() * 1000)


def main():
    conectar_wifi()

    cliente_vision = ClienteVision(config.VISION_HOST, config.VISION_PORT)
    cliente_vision.conectar()

    radio_rovers = ComunicacionRovers()
    control = ControladorMovimiento()
    sensores = Sensores()
    estimador_latencia = mundo.EstimadorLatencia()
    fsm = RoverFSM(config.MI_ARUCO_ID, config.COLOR_INICIAL)

    while True:
        msg = cliente_vision.leer_ultimo_mensaje()
        if msg is None:
            continue

        if not mundo.mensaje_utilizable(msg, ahora_ms(), estimador_latencia):
            # Version desconocida, fase que no permite actuar, o latencia
            # deteriorandose -- por seguridad, no se manda ningun comando nuevo.
            if msg.get("phase") != contrato.FASE_FINISHED:
                continue

        estado = fsm.transicion(
            msg,
            tiene_cubo=sensores.cubo_sujeto(),
            cubo_entregado=sensores.cubo_liberado_en_depot(),
        )

        if estado == ESTADO_DETENIDO:
            control.detener()
            continue

        rover = mundo.mi_rover(msg, fsm.mi_id)
        if rover is None:
            control.detener()
            continue

        if estado == ESTADO_APROXIMAR:
            cubo = mundo.cubo_por_color(msg, fsm.color_asignado)
            if cubo is not None:
                control.avanzar_hacia(rover, cubo)
        elif estado == ESTADO_TRANSPORTAR:
            depot = mundo.depot_por_color(msg, fsm.color_asignado)
            if depot is not None:
                control.avanzar_hacia(rover, depot)
        elif estado in (ESTADO_SUJETAR, ESTADO_ENTREGAR):
            control.detener()  # TODO: maniobra de agarre/entrega con las paletas
        # BUSCAR/OCIOSO: TODO decidir patron de espera/busqueda (p.ej. girar
        # despacio) en vez de quedarse quieto.


if __name__ == "__main__":
    main()
