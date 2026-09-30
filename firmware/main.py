"""Loop principal del rover (CircuitPython): leer telemetria, decidir, mover.

Toda la decision vive en comun.rover.ControladorRover (la misma que prueba el
simulador de pc_dev/). Aqui solo hay hardware: WiFi, TCP de vision, sensores y
motores, mas un paro de seguridad.
"""

from firmware import config
from firmware.comm_vision import ClienteVision
from firmware.motores import Motores
from firmware.sensores import Sensores

from comun import contrato, mundo
from comun.rover import ControladorRover

# Si no llega telemetria valida por mas de esto, se frenan los motores.
TIMEOUT_TELEMETRIA_MS = 500


def conectar_wifi():
    # Credenciales en settings.toml del dispositivo (no en el repo).
    import os
    import wifi

    wifi.radio.connect(
        os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD")
    )


def ahora_ms():
    # Contador monotonico (no epoca): EstimadorLatencia solo usa diferencias.
    import time
    return time.monotonic_ns() // 1000000


def main():
    motores = Motores()
    motores.detener()
    try:
        if not config.VISION_HOST:
            raise RuntimeError("Falta VISION_HOST en settings.toml del dispositivo")
        print("rover", config.MI_ARUCO_ID, "conectando WiFi...")
        conectar_wifi()
        cliente = ClienteVision(config.VISION_HOST, config.VISION_PORT)
        cliente.conectar()
        print("conectado a vision", config.VISION_HOST, config.VISION_PORT)

        sensores = Sensores()
        estimador = mundo.EstimadorLatencia()
        ctrl = ControladorRover(config.MI_ARUCO_ID, config.IDS_ROVERS)
        ultimo_ok = ahora_ms()
        estado_previo = None

        while True:
            msg = cliente.leer_ultimo_mensaje()
            ahora = ahora_ms()
            if msg is not None and (
                mundo.mensaje_utilizable(msg, ahora, estimador)
                or msg.get("phase") == contrato.FASE_FINISHED
            ):
                izq, der = ctrl.paso(msg, tiene_cubo=sensores.cubo_sujeto())
                motores.mover(izq, der)
                ultimo_ok = ahora
                if ctrl.estado != estado_previo:
                    print(msg.get("phase"), ctrl.estado, ctrl.fsm.color_asignado)
                    estado_previo = ctrl.estado
            elif ahora - ultimo_ok > TIMEOUT_TELEMETRIA_MS:
                motores.detener()
    finally:
        motores.detener()  # cualquier error o Ctrl-C deja los motores frenados


if __name__ == "__main__":
    main()
