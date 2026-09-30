#!/usr/bin/env python3
"""Copia comun/ y firmware/ al rover y deja firmware/code.py como /code.py.

NO toca /settings.toml ni /lib. REEMPLAZA /code.py: respaldalo antes con
respaldar_rover.py. Sin --si solo muestra que haria.

    python herramientas/desplegar.py COM3 --si
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import _rover

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("puerto")
    ap.add_argument("--si", action="store_true", help="ejecutar de verdad")
    a = ap.parse_args()

    archivos = []
    for carpeta in ("comun", "firmware"):
        for f in sorted(os.listdir(os.path.join(RAIZ, carpeta))):
            if f.endswith(".py") and f != "code.py":
                archivos.append((os.path.join(RAIZ, carpeta, f), ":%s/%s" % (carpeta, f)))
    archivos.append((os.path.join(RAIZ, "firmware", "code.py"), ":code.py"))

    print("Se copiarian %d archivos a %s (code.py se REEMPLAZA):" % (len(archivos), a.puerto))
    for _, d in archivos:
        print("  ", d)
    if not a.si:
        print("\n(simulacion: agrega --si para ejecutar)")
        return 0

    _rover.interrumpir(a.puerto)
    for carpeta in (":comun", ":firmware"):
        _rover.mpremote(a.puerto, "fs", "mkdir", carpeta)  # si ya existe, falla sin problema
    for origen, destino in archivos:
        cod, salida = _rover.mpremote(a.puerto, "fs", "cp", origen, destino)
        if cod != 0:
            print("ERROR copiando", destino, salida)
            return 1
    print("Listo. Reinicia el rover (boton o desenchufar) para que arranque code.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
