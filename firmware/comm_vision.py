"""Cliente TCP NDJSON del sistema de vision, para MicroPython (ESP32).

Implementa el buffering de lineas y la politica de "quedarse solo con el
ultimo mensaje" del contrato (Reglas 1 y 3 -- ver docs/contrato_telemetria.md).
Usa unicamente el modulo `socket`, disponible en el port ESP32 de MicroPython.
"""

import json
import socket


class ClienteVision:
    def __init__(self, host, port, tamano_buffer=4096):
        self.host = host
        self.port = port
        self.tamano_buffer = tamano_buffer
        self._sock = None
        self._buffer = b""

    def conectar(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(socket.getaddrinfo(self.host, self.port)[0][-1])
        self._buffer = b""

    def cerrar(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def leer_ultimo_mensaje(self):
        """Drena todo lo disponible en el socket y devuelve solo el ULTIMO
        mensaje completo (dict) que haya llegado, descartando los anteriores
        en el mismo drenado (politica de buffer unico, Regla 3).

        Devuelve None si no hay ningun mensaje completo nuevo todavia.

        TODO: en MicroPython, poner el socket en no bloqueante
        (self._sock.setblocking(False)) para que esto no trabe el loop
        principal cuando no hay datos aun.
        """
        try:
            chunk = self._sock.recv(self.tamano_buffer)
        except OSError:
            # EAGAIN/EWOULDBLOCK en socket no bloqueante: no hay datos todavia.
            chunk = b""

        if chunk:
            self._buffer += chunk

        ultimo = None
        while b"\n" in self._buffer:
            linea, self._buffer = self._buffer.split(b"\n", 1)
            if not linea.strip():
                continue
            try:
                ultimo = json.loads(linea)
            except ValueError:
                # Linea corrupta/incompleta -- se ignora, ya se habra
                # recibido/recibira una valida en el proximo frame (20Hz).
                continue
        return ultimo
