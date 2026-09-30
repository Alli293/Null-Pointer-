"""Configuracion por rover (CircuitPython / IdeaBoard).

Pines tomados del codigo de fabrica de la IdeaBoard (ver rover_original/).
Las credenciales WiFi NO van aqui: viven en settings.toml del dispositivo
(CIRCUITPY_WIFI_SSID / CIRCUITPY_WIFI_PASSWORD), que no se sube al repo.
"""

# --- Identidad de este rover -------------------------------------------------
# Mismo archivo para los dos rovers: cada uno se reconoce por la MAC de su radio
# (leida con `wifi.radio.mac_address`). El reparto de colores sale del ID
# (comun/protocolo_rovers.asignacion_estatica). El ID es el del marcador ArUco fisico
# (diccionario 4X4), decodificado de fotos de los stickers.
ROVERS = {
    (224, 140, 254, 37, 199, 72): {"id": 10},    # rover 1 (COM3 en banco)
    (224, 140, 254, 39, 166, 120): {"id": 11},   # rover 2 (COM12 en banco)
}


def _yo():
    import wifi
    mac = tuple(wifi.radio.mac_address)
    if mac not in ROVERS:
        raise RuntimeError("MAC desconocida %r: agregarla a config.ROVERS" % (mac,))
    return mac


_MI_MAC = _yo()
MI_ARUCO_ID = ROVERS[_MI_MAC]["id"]
IDS_ROVERS = sorted(r["id"] for r in ROVERS.values())
# MAC del OTRO rover, para ESP-NOW.
MAC_OTRO_ROVER = next(bytes(m) for m in ROVERS if m != _MI_MAC)

# --- Red ---------------------------------------------------------------------
# IP de la PC con el sistema de vision (nunca 127.0.0.1) y su puerto. Se leen del
# settings.toml del dispositivo (ver firmware/settings.toml.example) para no
# reflashear codigo cada vez que cambia la red.
import os

VISION_HOST = os.getenv("VISION_HOST")
VISION_PORT = os.getenv("VISION_PORT") or 2026

# --- Motores (IdeaBoard: motor_1 = IO12/IO14, motor_2 = IO13/IO15) -----------
MOTOR_IZQ = 1             # TODO: confirmar cual motor es el izquierdo en el chasis
MOTOR_DER = 2
INVERTIR_IZQ = False      # TODO: True si el motor gira al reves al montarse
INVERTIR_DER = False

# --- Sensores ----------------------------------------------------------------
PIN_ULTRASONICO_TRIG = "IO26"   # ejemplo de fabrica code_ultrasonic.py
PIN_ULTRASONICO_ECHO = "IO25"
PIN_IR = "IO33"                 # ejemplo de fabrica code_IR.py (ojo: code.py de
                                # prueba usa IO33 para un NeoPixel; confirmar cableado)
DISTANCIA_AGARRE_CM = 4.0       # TODO: calibrar -- cubo "dentro" de las paletas

# --- Suavidad ----------------------------------------------------------------
# Multiplica las velocidades de crucero y de empuje del planificador. Empezar
# SUAVE (0.5) y subir a 1.0 cuando todo funcione. Si a este valor las ruedas ni
# arrancan (potencia por debajo de la minima del motor), subirlo de a poco.
FACTOR_VELOCIDAD = 0.5
