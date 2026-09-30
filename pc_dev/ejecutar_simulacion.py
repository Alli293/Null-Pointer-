#!/usr/bin/env python3
"""Corre el ControladorRover de comun/ (el mismo que el firmware) contra un publisher
real de telemetria (p.ej. mock_publisher.py del repo guia), SIN ESP32 ni motores.

Imprime los cambios de estado y los comandos de rueda que el rover "mandaria".
Ojo: el mock_publisher NO reacciona a esos comandos (publica un mundo que evoluciona
solo), asi que sirve para ver la decision en vivo, no para cerrar el lazo. Para el
lazo cerrado usar pc_dev/simulador_fisico.py (pytest).

Ver simulacion/README.md. Uso:
    python ejecutar_simulacion.py --host 127.0.0.1 --port 2026 --id 10
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comun import contrato, mundo
from comun.rover import ControladorRover

from cliente_vision_sim import ClienteVision


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--host", required=True, help="IP de la PC que corre el sistema de vision")
    parser.add_argument("--port", type=int, default=2026)
    parser.add_argument("--id", type=int, required=True, help="ID de marcador ArUco de este rover")
    parser.add_argument("--ids", default="10,11", help="IDs de los dos rovers (reparte los colores)")
    parser.add_argument("--cada", type=int, default=10, help="imprimir cada N mensajes (a 20Hz, 10 = ~2 veces/seg)")
    args = parser.parse_args()

    ids = [int(x) for x in args.ids.split(",")]
    cliente = ClienteVision(args.host, args.port)
    cliente.conectar()
    ctrl = ControladorRover(args.id, ids)
    print(f"Conectado a {args.host}:{args.port}, rover id={args.id}, color inicial={ctrl.fsm.color_asignado}")

    estimador_latencia = mundo.EstimadorLatencia()
    contador = 0
    estado_previo = None
    try:
        while True:
            msg = cliente.leer_mensaje()
            contador += 1

            utilizable = mundo.mensaje_utilizable(msg, int(time.time() * 1000), estimador_latencia)
            if utilizable or msg.get("phase") == contrato.FASE_FINISHED:
                izq, der = ctrl.paso(msg)
            else:
                izq, der = 0.0, 0.0

            if ctrl.estado != estado_previo:
                print(f"[seq={msg.get('seq')}] fase={msg.get('phase')} -> estado: {estado_previo} -> {ctrl.estado}")
                estado_previo = ctrl.estado

            if contador % args.cada == 0:
                rover = mundo.mi_rover(msg, args.id)
                print(
                    f"  seq={msg.get('seq')} fase={msg.get('phase')} estado={ctrl.estado} "
                    f"color={ctrl.fsm.color_asignado} ruedas=({izq:+.2f},{der:+.2f}) rover={rover}"
                )
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
    finally:
        cliente.cerrar()


if __name__ == "__main__":
    main()
