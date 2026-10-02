#!/usr/bin/env python3
"""Prueba corta de motores: cada motor 1.5 s hacia adelante, uno por uno.

PELIGRO: mueve las ruedas. Levantar el rover (ruedas en el aire) y encender las
baterias de motores. Exige --ruedas-en-el-aire para correr.

    python herramientas/probar_motores.py COM3 --ruedas-en-el-aire [--potencia 0.4]

Resultado esperado en nuestros rovers: motor_1 = rueda IZQUIERDA, motor_2 = DERECHA,
ambas hacia adelante (ver config.MOTOR_IZQ / MOTOR_DER / INVERTIR_*).
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import _rover

CODIGO = """
import time
from ideaboard import IdeaBoard
ib = IdeaBoard()
try:
    for n, m in ((1, ib.motor_1), (2, ib.motor_2)):
        print('MOTOR', n, 'adelante')
        m.throttle = %f
        time.sleep(1.5)
        m.throttle = 0.0
        time.sleep(0.8)
finally:
    ib.motor_1.throttle = 0.0
    ib.motor_2.throttle = 0.0
    print('frenado')
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("puerto")
    ap.add_argument("--ruedas-en-el-aire", action="store_true", help="confirmo que el rover esta levantado")
    ap.add_argument("--potencia", type=float, default=0.4)
    a = ap.parse_args()
    if not a.ruedas_en_el_aire:
        print("Falta --ruedas-en-el-aire: levanta el rover y confirma.")
        return 2
    if not 0 < a.potencia <= 0.6:
        print("Potencia fuera de rango (0 < p <= 0.6 para pruebas).")
        return 2
    cod, salida = _rover.ejecutar(a.puerto, CODIGO % a.potencia)
    print(salida)
    return cod


if __name__ == "__main__":
    sys.exit(main())
