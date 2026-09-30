#!/usr/bin/env python3
"""Recorre los estados del LED de un rover (cada uno N segundos) para verlos con los ojos.

Requiere el firmware desplegado (usa firmware/indicador.py del rover). No mueve motores.
Interrumpe el programa que corra el rover; reinicialo despues para que vuelva a arrancar.

    python herramientas/probar_led.py COM12
    python herramientas/probar_led.py COM12 --segundos 5 --estados esperando,TRANSPORTAR
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import _rover

ORDEN = ("conectando", "esperando", "sin_telemetria", "error", "APROXIMAR", "SUJETAR",
         "TRANSPORTAR", "ENTREGAR", "BUSCAR", "OCIOSO", "DETENIDO")

CODIGO = """
import time
from firmware.indicador import Indicador, COLORES
ind = Indicador()
time.sleep(4)
for i, clave in enumerate(%r, 1):
    color, patron = COLORES[clave]
    print(i, clave, color, patron)
    ind.mostrar(clave)
    fin = time.monotonic() + %f
    while time.monotonic() < fin:
        ind.actualizar()
        time.sleep(0.01)
    ind.mostrar('apagado')
    time.sleep(1.5)
print('fin')
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("puerto")
    ap.add_argument("--segundos", type=float, default=4.0, help="duracion de cada estado")
    ap.add_argument("--estados", default=",".join(ORDEN), help="lista separada por comas")
    a = ap.parse_args()
    estados = tuple(e.strip() for e in a.estados.split(",") if e.strip())
    desconocidos = [e for e in estados if e not in ORDEN]
    if desconocidos:
        print("Estados desconocidos:", desconocidos, "\nValidos:", ", ".join(ORDEN))
        return 2
    print("Empieza en 4 s. Orden:", ", ".join("%d %s" % (i, e) for i, e in enumerate(estados, 1)))
    _rover.interrumpir(a.puerto)
    cod, salida = _rover.mpremote(a.puerto, "exec", CODIGO % (estados, a.segundos),
                                  timeout=int(len(estados) * (a.segundos + 2) + 40))
    print(salida)
    return cod


if __name__ == "__main__":
    sys.exit(main())
