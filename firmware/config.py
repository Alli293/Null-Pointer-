"""Configuracion por rover. Copiar/editar este archivo por robot antes de
flashear -- valores reales pendientes de banco de pruebas (ver robot.md /
conexiones/ del repo guia para el pinout exacto del kit).
"""

# --- Identidad de este rover -------------------------------------------------
MI_ARUCO_ID = 10          # TODO: 10 u 11 segun el marcador fisico pegado al robot
COLOR_INICIAL = "green"   # color con el que arranca este rover (ver
                           # comun/protocolo_rovers.asignacion_estatica)

# --- Red ---------------------------------------------------------------------
WIFI_SSID = "TODO"
WIFI_PASSWORD = "TODO"
VISION_HOST = "TODO"      # IP de la PC que corre el sistema de vision (nunca 127.0.0.1)
VISION_PORT = 2026

# --- Pines de motor (placeholder -- confirmar con conexiones/README.md) ------
PIN_MOTOR_IZQ_A = None     # TODO
PIN_MOTOR_IZQ_B = None     # TODO
PIN_MOTOR_DER_A = None     # TODO
PIN_MOTOR_DER_B = None     # TODO

# --- Pines de sensores (placeholder) ------------------------------------------
PINES_IR = (None, None, None, None)   # TODO: 4 sensores infrarrojos
PIN_ULTRASONICO_TRIG = None            # TODO
PIN_ULTRASONICO_ECHO = None            # TODO
PIN_SENSOR_COLOR_SDA = None            # TODO
PIN_SENSOR_COLOR_SCL = None            # TODO
