"""Utilidades comunes para hablar con los rovers por USB (CircuitPython + mpremote).

Requiere `pip install mpremote` (trae pyserial). Se usa siempre como
`python -m mpremote`, porque el ejecutable `mpremote` suele no estar en el PATH en Windows.
"""

import subprocess
import sys
import time


def puertos():
    """Lista de puertos serie detectados por mpremote: [(puerto, descripcion)]."""
    r = subprocess.run([sys.executable, "-m", "mpremote", "connect", "list"],
                       capture_output=True, text=True)
    salida = []
    for linea in r.stdout.splitlines():
        partes = linea.split(None, 1)
        if partes:
            salida.append((partes[0], partes[1] if len(partes) > 1 else ""))
    return salida


def interrumpir(puerto):
    """Manda Ctrl-C para sacar al rover del code.py que este corriendo (algunos
    tienen un bucle infinito y mpremote no logra entrar al REPL sin esto)."""
    import serial
    with serial.Serial(puerto, 115200, timeout=1) as s:
        for _ in range(4):
            s.write(b"\x03")
            time.sleep(0.3)
        s.read(2000)


def mpremote(puerto, *args, timeout=60):
    """Corre `mpremote connect <puerto> <args>` y devuelve (codigo, salida)."""
    r = subprocess.run([sys.executable, "-m", "mpremote", "connect", puerto, *args],
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def ejecutar(puerto, codigo, timeout=60):
    """Ejecuta codigo Python en el rover (desde RAM, sin guardar nada)."""
    interrumpir(puerto)
    return mpremote(puerto, "exec", codigo, timeout=timeout)
