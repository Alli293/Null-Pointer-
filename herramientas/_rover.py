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


def subir(puerto, local, remoto):
    """Copia un archivo al rover escribiendolo con open() desde un exec.

    `mpremote fs cp` falla en CircuitPython con "OSError: [Errno 2]" cuando el archivo
    destino todavia NO existe (solo funciona si ya existia, p. ej. el settings.toml de
    fabrica). Esto crea las carpetas, escribe el contenido y verifica el tamano.
    Devuelve (ok, mensaje). `remoto` sin ":" inicial, p. ej. "comun/rover.py".
    """
    import base64

    with open(local, "rb") as f:
        datos = f.read()
    if local.endswith(".py"):
        datos = datos.replace(b"\r\n", b"\n")  # git en Windows puede dejarlos en CRLF
    b64 = base64.b64encode(datos).decode()
    codigo = (
        "import os, binascii\n"
        "destino = %r\n"
        "ruta = ''\n"
        "for parte in destino.split('/')[:-1]:\n"
        "    ruta += '/' + parte\n"
        "    try:\n"
        "        os.mkdir(ruta)\n"
        "    except OSError:\n"
        "        pass\n"
        "f = open('/' + destino, 'wb')\n"
        "f.write(binascii.a2b_base64(%r))\n"
        "f.close()\n"
        "print(os.stat('/' + destino)[6])\n"
    ) % (remoto, b64)
    cod, salida = mpremote(puerto, "exec", codigo)
    if cod != 0:
        return False, salida[-300:]
    if salida.strip().splitlines()[-1].strip() != str(len(datos)):
        return False, "tamano distinto: rover=%s local=%d" % (salida.strip()[-20:], len(datos))
    return True, "%d bytes" % len(datos)


def ejecutar(puerto, codigo, timeout=60):
    """Ejecuta codigo Python en el rover (desde RAM, sin guardar nada)."""
    interrumpir(puerto)
    return mpremote(puerto, "exec", codigo, timeout=timeout)
