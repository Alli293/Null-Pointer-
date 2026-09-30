"""Comunicacion rover-a-rover via ESP-NOW (modulo `espnow` de CircuitPython 9).

Usa el formato de mensaje de comun/protocolo_rovers.py. La negociacion robusta
ante mensajes perdidos sigue pendiente (ver docs/arquitectura.md).
"""

import json

import espnow


class ComunicacionRovers:
    def __init__(self, mac_otro_rover=None):
        self._e = espnow.ESPNow()
        self._peer = None
        if mac_otro_rover is not None:
            self._peer = espnow.Peer(mac=bytes(mac_otro_rover))
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
        try:
            return json.loads(paquete.msg)
        except ValueError:
            return None
