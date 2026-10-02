"""Cliente TCP NDJSON de escritorio (CPython) para el sistema de vision.

Misma logica que firmware/comm_vision.py (buffering + quedarse con el ultimo
mensaje), pero usando el `socket` estandar de CPython para correr en la PC sin
tocar el robot -- pensado para iterar rapido y para ejecutar_simulacion.py.
"""

import json
import socket


class ClienteVision:
    def __init__(self, host, port, tamano_buffer=4096, timeout_s=2.0):
        self.host = host
        self.port = port
        self.tamano_buffer = tamano_buffer
        self.timeout_s = timeout_s
        self._sock = None
        self._buffer = b""

    def conectar(self):
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout_s)
        self._buffer = b""

    def cerrar(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def leer_mensaje(self):
        """Bloquea hasta tener UNA linea completa y la devuelve parseada.

        A diferencia de firmware/comm_vision.py (que drena todo el buffer y se
        queda con el ultimo), esta version devuelve mensaje por mensaje -- util
        para inspeccionar cada frame en ejecutar_simulacion.py. Para replicar
        la politica de "solo el ultimo" en la PC, ver leer_ultimo_disponible().
        """
        while b"\n" not in self._buffer:
            chunk = self._sock.recv(self.tamano_buffer)
            if not chunk:
                raise ConnectionError("El sistema de vision cerro la conexion")
            self._buffer += chunk
        linea, self._buffer = self._buffer.split(b"\n", 1)
        return json.loads(linea)

    def leer_ultimo_disponible(self):
        """Version no bloqueante equivalente a firmware/comm_vision.py: drena
        lo que haya en el socket ahora mismo y devuelve solo el ultimo mensaje
        completo (o None si no llego nada nuevo todavia)."""
        self._sock.setblocking(False)
        try:
            chunk = self._sock.recv(self.tamano_buffer)
            if chunk:
                self._buffer += chunk
        except BlockingIOError:
            pass
        finally:
            self._sock.setblocking(True)

        ultimo = None
        while b"\n" in self._buffer:
            linea, self._buffer = self._buffer.split(b"\n", 1)
            if linea.strip():
                ultimo = json.loads(linea)
        return ultimo
