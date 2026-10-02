#!/usr/bin/env python3
"""Lista los rovers conectados por USB y muestra su UID y su MAC.

Solo lectura: no modifica nada en el rover.

    python herramientas/info_rover.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import _rover

CODIGO = """
import wifi
print(open('/boot_out.txt').read().strip().replace(chr(10), ' | '))
print('MAC', list(wifi.radio.mac_address))
"""


def main():
    ps = _rover.puertos()
    if not ps:
        print("No hay puertos. Conecta un rover por USB y cierra Thonny.")
        return 1
    for puerto, desc in ps:
        print("==", puerto, desc)
        cod, salida = _rover.ejecutar(puerto, CODIGO)
        print(salida if cod == 0 else "  (no se pudo leer: %s)" % salida[-200:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
