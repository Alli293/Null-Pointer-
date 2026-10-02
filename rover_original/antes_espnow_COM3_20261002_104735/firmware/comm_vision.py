"""Adaptador: conserva el transporte del usuario y vigila secuencias nuevas."""
import time
import socketpool
import wifi
from firmware import tcp_usuario as tcp
from firmware.buffer_ndjson import BufferNDJSON

class ClienteVision:
    def __init__(self, host, port, tamano_buffer=4096):
        self.host = host
        self.port = port
        self._pool = socketpool.SocketPool(wifi.radio)
        self._sock = None
        self._buf = BufferNDJSON()
        self._seq = None
        self._nuevo = time.monotonic()

    def conectar(self):
        self.cerrar()
        self._sock = tcp.abrir_tcp(self._pool)
        if self._sock is None:
            raise OSError("No se pudo conectar con vision")
        self._nuevo = time.monotonic()

    def cerrar(self):
        self._sock = tcp.cerrar(self._sock)
        self._buf.limpiar()
        self._seq = None

    def leer_ultimo_mensaje(self):
        if self._sock is None or not tcp.drenar_tcp(self._sock, self._buf):
            self.cerrar()
            raise OSError("Conexion de vision perdida")
        msg = self._buf.ultimo()
        ahora = time.monotonic()
        if msg is not None and isinstance(msg.get("seq"), int) and msg["seq"] != self._seq:
            self._seq = msg["seq"]
            self._nuevo = ahora
            return msg
        if ahora - self._nuevo >= 0.75:
            self.cerrar()
            raise OSError("Vision sin secuencia nueva durante 0.75 s")
        return None
