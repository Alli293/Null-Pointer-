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
        self._pool = socketpool.SocketPool(wifi.radio)

    def conectar(self):
        self.cerrar()
        self._sock = self._pool.socket(self._pool.AF_INET, self._pool.SOCK_STREAM)
        try:
            self._sock.settimeout(3)
            self._sock.connect((self.host, int(self.port)))
            self._sock.setblocking(False)
        except BaseException:
            self.cerrar()
            raise
        self._buffer = b""

    def cerrar(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def leer_ultimo_mensaje(self):
        """Devuelve el ultimo mensaje dict completo, o None si no hay nuevo."""
        try:
            n = self._sock.recv_into(self._rx)
        except OSError as exc:
            if exc.args and exc.args[0] in (11, 35):  # EAGAIN/EWOULDBLOCK
                return None
            self.cerrar()
            raise
        if n == 0:
            self.cerrar()
            raise OSError("Vision cerro la conexion")
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
