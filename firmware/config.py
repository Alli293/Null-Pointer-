"""Configuracion por rover (CircuitPython / IdeaBoard).

Pines tomados del codigo de fabrica de la IdeaBoard (ver rover_original/).
Las credenciales WiFi NO van aqui: viven en settings.toml del dispositivo
(CIRCUITPY_WIFI_SSID / CIRCUITPY_WIFI_PASSWORD), que no se sube al repo.
"""

# --- Identidad de este rover -------------------------------------------------
MI_ARUCO_ID = 10          # TODO: 10 u 11 segun el marcador fisico pegado al robot
COLOR_INICIAL = "green"   # ver comun/protocolo_rovers.asignacion_estatica

# MAC del OTRO rover para ESP-NOW (bytes de 6). TODO: leerla de cada placa con
# `import wifi; wifi.radio.mac_address`.
MAC_OTRO_ROVER = None

# --- Red ---------------------------------------------------------------------
VISION_HOST = "TODO"      # IP de la PC con el sistema de vision (nunca 127.0.0.1)
VISION_PORT = 2026

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
