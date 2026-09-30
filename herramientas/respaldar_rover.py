#!/usr/bin/env python3
"""Copia a rover_original/<nombre>/ los archivos propios del rover (no /lib).

Solo lectura. Hacerlo SIEMPRE antes de desplegar por primera vez.

    python herramientas/respaldar_rover.py COM3 rover1
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import _rover

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVOS = ["boot_out.txt", "boot.py", "code.py", "main.py", "prueba.py", "settings.toml"]


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    puerto, nombre = sys.argv[1], sys.argv[2]
    destino = os.path.join(RAIZ, "rover_original", nombre)
    os.makedirs(destino, exist_ok=True)
    _rover.interrumpir(puerto)
    for f in ARCHIVOS:
        cod, _ = _rover.mpremote(puerto, "fs", "cp", ":/" + f, os.path.join(destino, f))
        print(("copiado " if cod == 0 else "no existe ") + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
