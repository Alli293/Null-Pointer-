"""Comunicacion rover-a-rover via ESP-NOW.

Adaptar de codigos/espnow_bidirectional.py (repo guia). Usa el formato de
mensaje de comun/protocolo_rovers.py para que ambos lados (PC de simulacion en
pruebas de logica, y ESP32 real) hablen el mismo dict.

TODO: la libreria `espnow` de MicroPython (modulo nativo del port ESP32) da
send()/recv() a nivel de bytes -- aca falta el (de)serializador y el registro
de la MAC del otro rover como peer.
"""

import json


class ComunicacionRovers:
    def __init__(self, mac_otro_rover=None):
        self.mac_otro_rover = mac_otro_rover
        # TODO: import espnow; self._e = espnow.ESPNow(); self._e.active(True);
        # self._e.add_peer(mac_otro_rover)

    def enviar(self, mensaje_dict):
        payload = json.dumps(mensaje_dict).encode("utf-8")
        # TODO: self._e.send(self.mac_otro_rover, payload)

    def recibir_no_bloqueante(self):
        """Devuelve el proximo mensaje dict recibido, o None si no hay nada
        nuevo. No debe bloquear -- el loop principal en main.py es de un solo
        hilo y tambien tiene que leer telemetria de vision."""
        # TODO: mac, payload = self._e.irecv(0); parsear payload con json.loads
        return None
