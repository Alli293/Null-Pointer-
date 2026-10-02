"""Loop principal del rover (CircuitPython): leer telemetria, decidir, mover.

Toda la decision vive en comun.rover.ControladorRover (la misma que prueba el
simulador de pc_dev/). Aqui solo hay hardware: WiFi, TCP de vision, sensores y
motores, mas un paro de seguridad.
"""

from firmware import config
from firmware.comm_vision import ClienteVision
from firmware.comm_espnow import ComunicacionRovers
from comun.coordinacion import Coordinador
from firmware.indicador import Indicador
from firmware.motores import Motores
from firmware.sensores import Sensores

from comun import contrato, mundo
from comun.planificador import Planificador, VEL_CRUCERO, VEL_EMPUJE
from comun.maquina_estados import ESTADO_DETENIDO, ESTADO_OCIOSO
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


def conectar_vision(cliente, motores, indicador):
    import time
    while True:
        motores.detener()
        indicador.mostrar("sin_telemetria")
        print("conectando a vision", cliente.host, cliente.port)
        try:
            cliente.conectar()
            return
        except OSError as exc:
            print("Vision no disponible:", exc,
                  "Revisar IP, servidor TCP 2026 y firewall. Reintento en 2 s.")
            time.sleep(2)


def main():
    motores = Motores()
    motores.detener()
    indicador = Indicador()
    indicador.mostrar("conectando")
    try:
        if not config.VISION_HOST:
            raise RuntimeError("Falta VISION_HOST en settings.toml del dispositivo")
        print("rover", config.MI_ARUCO_ID, "conectando WiFi...")
        conectar_wifi()
        import os
        radio = ComunicacionRovers(config.MAC_OTRO_ROVER)
        coord = Coordinador(config.MI_MAC, config.MAC_OTRO_ROVER,
                            config.IDS_ROVERS, config.MI_ARUCO_ID,
                            "".join("%02x" % b for b in os.urandom(8)))
        print("MAC48", coord.mac, "lider" if coord.lider else "seguidor")
        cliente = ClienteVision(config.VISION_HOST, config.VISION_PORT)
        conectar_vision(cliente, motores, indicador)
        print("conectado a vision", config.VISION_HOST, config.VISION_PORT)
        indicador.mostrar("esperando")

        sensores = Sensores()
        estimador = mundo.EstimadorLatencia()
        planificador = Planificador(
            vel_crucero=VEL_CRUCERO * config.FACTOR_VELOCIDAD,
            vel_empuje=VEL_EMPUJE * config.FACTOR_VELOCIDAD,
        )
        ctrl = ControladorRover(config.MI_ARUCO_ID, config.IDS_ROVERS, planificador,
                               coordinado=True)
        ultimo_ok = ahora_ms()
        ultimo_tx = -1000
        estado_previo = None

        while True:
            indicador.actualizar()  # parpadeos del LED
            try:
                msg = cliente.leer_ultimo_mensaje()
            except OSError:
                motores.detener()
                conectar_vision(cliente, motores, indicador)
                estimador.reset()
                ultimo_ok = ahora_ms()
                continue
            ahora = ahora_ms()
            if msg is not None and (not isinstance(msg, dict) or msg.get("v") != 2):
                motores.detener()
                msg = None
            for _ in range(8):
                paquete = radio.recibir_no_bloqueante()
                if paquete is None:
                    break
                coord.recibir(paquete, ahora)
            terminado = ctrl.fsm.color_asignado is None or ctrl.estado == ESTADO_OCIOSO
            if ahora - ultimo_tx >= 100:
                try:
                    radio.enviar(coord.mensaje(terminado))
                except OSError:
                    motores.detener()
                ultimo_tx = ahora
            if msg is not None and (
                mundo.mensaje_utilizable(msg, ahora, estimador)
                or msg.get("phase") in (contrato.FASE_FINISHED, contrato.FASE_IDLE)
            ):
                coord.actualizar(msg, ahora, terminado)
                ctrl.asignar(coord.plan[coord.indice])
                if coord.autorizado(ahora):
                    izq, der = ctrl.paso(msg, tiene_cubo=sensores.cubo_sujeto())
                else:
                    izq, der = 0.0, 0.0
                motores.mover(izq, der)
                ultimo_ok = ahora
                # LED: el estado del FSM solo cuando la ronda esta en juego (o terminada).
                if msg.get("phase") == contrato.FASE_RUNNING or ctrl.estado == ESTADO_DETENIDO:
                    indicador.mostrar(ctrl.estado)
                else:
                    indicador.mostrar("esperando")
                if ctrl.estado != estado_previo:
                    print(msg.get("phase"), ctrl.estado, ctrl.fsm.color_asignado)
                    estado_previo = ctrl.estado
            elif (ahora - ultimo_ok > TIMEOUT_TELEMETRIA_MS or
                  not coord.autorizado(ahora)):
                motores.detener()
                indicador.mostrar("sin_telemetria")
    except Exception:
        indicador.mostrar("error")
        raise
    finally:
        motores.detener()  # cualquier error o Ctrl-C deja los motores frenados


if __name__ == "__main__":
    main()
