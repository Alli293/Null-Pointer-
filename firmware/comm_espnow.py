"""Comunicacion rover-a-rover via ESP-NOW, para CircuitPython.

Usa el formato de mensaje de comun/protocolo_rovers.py (dict -> JSON) para que
ambos lados hablen el mismo formato. El truco de start_ap()/stop_ap() para
fijar el canal sin asociarse a ningun WiFi real, y el patron de Peer/send/read,
quedaron verificados en banco con los dos CenfoBots hablandose en ambas
direcciones (ver docs/arquitectura.md).
"""

import json
import wifi
import espnow

from firmware import config


class ComunicacionRovers:
    def __init__(self, mac_otro_rover=None, canal=None):
        mac_str = mac_otro_rover if mac_otro_rover is not None else config.PEER_MAC
        canal = canal if canal is not None else config.ESPNOW_CHANNEL

        # Fija el canal del radio sin conectarse a ningun WiFi real -- necesario
        # para que ambos rovers terminen en el mismo canal ESP-NOW (verificado
        # en banco: sin esto, o con el WiFi de vision ya conectado en otro
        # canal, los mensajes no llegan).
        wifi.radio.start_ap(" ", "", channel=canal, max_connections=0)
        wifi.radio.stop_ap()

        self._esp = espnow.ESPNow()
        peer_mac = bytes(int(b, 16) for b in mac_str.split(":"))
        self._peer = espnow.Peer(mac=peer_mac, channel=canal)
        self._esp.peers.append(self._peer)

    def enviar(self, mensaje_dict):
        payload = json.dumps(mensaje_dict).encode("utf-8")
        try:
            self._esp.send(payload, self._peer)
        except Exception:
            # Radio ocupada o peer sin responder -- se reintenta en el
            # proximo ciclo del loop principal, no vale la pena reventar el
            # rover por un mensaje perdido (ver docs/contrato_telemetria.md,
            # "huecos son normales").
            pass

    def recibir_no_bloqueante(self):
        """Devuelve el proximo mensaje dict recibido, o None si no hay nada
        nuevo. No bloquea -- el loop principal en main.py es de un solo hilo
        y tambien tiene que leer telemetria de vision."""
        packet = self._esp.read()
        if packet is None:
            return None
        try:
            return json.loads(packet.msg.decode("utf-8"))
        except ValueError:
            return None
