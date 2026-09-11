#!/usr/bin/env python3
"""Corre la logica de comun/ (validacion + RoverFSM) contra un publisher real de
telemetria (p.ej. mock_publisher.py del repo guia) sin necesitar ningun ESP32.

Ver simulacion/README.md para levantar el publisher simulado.

Uso:
    python ejecutar_simulacion.py --host 127.0.0.1 --port 2026 --id 10 --color green
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comun import contrato, mundo
from comun.maquina_estados import RoverFSM

from cliente_vision_sim import ClienteVision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="IP de la PC que corre el sistema de vision")
    parser.add_argument("--port", type=int, default=2026)
    parser.add_argument("--id", type=int, required=True, help="ID de marcador ArUco de este rover")
    parser.add_argument("--color", required=True, choices=("red", "green", "blue"))
    parser.add_argument("--cada", type=int, default=10, help="imprimir cada N mensajes (a 20Hz, 10 = ~2 veces/seg)")
    args = parser.parse_args()

    cliente = ClienteVision(args.host, args.port)
    cliente.conectar()
    print(f"Conectado a {args.host}:{args.port}, simulando rover id={args.id} color={args.color}")

    estimador_latencia = mundo.EstimadorLatencia()
    fsm = RoverFSM(args.id, args.color)

    contador = 0
    estado_previo = None
    try:
        while True:
            msg = cliente.leer_mensaje()
            contador += 1

            utilizable = mundo.mensaje_utilizable(msg, int(time.time() * 1000), estimador_latencia)
            estado = fsm.transicion(msg) if utilizable or msg.get("phase") == contrato.FASE_FINISHED else fsm.estado

            if estado != estado_previo:
                print(f"[seq={msg.get('seq')}] fase={msg.get('phase')} -> estado FSM: {estado_previo} -> {estado}")
                estado_previo = estado

            if contador % args.cada == 0:
                rover = mundo.mi_rover(msg, args.id)
                cubo = mundo.cubo_por_color(msg, args.color)
                print(
                    f"  seq={msg.get('seq')} rover={rover} "
                    f"cubo_{args.color}={cubo} estado={estado} utilizable={utilizable}"
                )
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
    finally:
        cliente.cerrar()


if __name__ == "__main__":
    main()
