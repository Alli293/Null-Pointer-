"""Cliente TCP NDJSON del sistema de vision para CircuitPython (ESP32).

Usa wifi + socketpool. Buffer unico: solo devuelve el ULTIMO mensaje completo
(Reglas 1 y 3 -- ver docs/contrato_telemetria.md).
"""

import json

import socketpool
import wifi


class ClienteVision:
    def __init__(self, host, port, tamano_buffer=4096):
        self.host = host
        self.port = port
        self._rx = bytearray(tamano_buffer)
        self._sock = None
        self._buffer = b""

    def conectar(self):
        pool = socketpool.SocketPool(wifi.radio)
        self._sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        self._sock.connect((self.host, self.port))
        self._sock.setblocking(False)
        self._buffer = b""

    def cerrar(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def leer_ultimo_mensaje(self):
        """Devuelve el ultimo mensaje dict completo, o None si no hay nuevo."""
        try:
            n = self._sock.recv_into(self._rx)
        except OSError:
            n = 0  # EAGAIN: sin datos todavia
        if n:
            self._buffer += bytes(self._rx[:n])

        ultimo = None
        while b"\n" in self._buffer:
            linea, self._buffer = self._buffer.split(b"\n", 1)
            if not linea.strip():
                continue
            try:
                ultimo = json.loads(linea)
            except ValueError:
                continue  # linea corrupta: llega otra valida en el proximo frame
        return ultimo
