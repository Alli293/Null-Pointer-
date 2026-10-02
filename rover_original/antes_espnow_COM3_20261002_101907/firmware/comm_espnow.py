"""Comunicacion rover-a-rover via ESP-NOW (modulo `espnow` de CircuitPython 9).

Transporta los estados y planes de comun/coordinacion.py.
"""

import json

import espnow


class ComunicacionRovers:
    def __init__(self, mac_otro_rover=None):
        self._e = espnow.ESPNow()
        self._peer = None
        self._mac = bytes(mac_otro_rover) if mac_otro_rover is not None else None
        if mac_otro_rover is not None:
            self._peer = espnow.Peer(mac=bytes(mac_otro_rover), channel=0)
            self._e.peers.append(self._peer)

    def enviar(self, mensaje_dict):
        if self._peer is None:
            return
        self._e.send(json.dumps(mensaje_dict).encode("utf-8"), self._peer)

    def recibir_no_bloqueante(self):
        """Proximo mensaje dict recibido, o None. No bloquea."""
        if len(self._e) == 0:
            return None
        paquete = self._e.read()
        if paquete is None or bytes(paquete.mac) != self._mac:
            return None
        try:
            resultado = json.loads(paquete.msg)
            return resultado if isinstance(resultado, dict) else None
        except ValueError:
            return None
