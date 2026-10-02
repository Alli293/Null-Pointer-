"""Configuracion por rover. Copiar/editar este archivo por robot antes de
correrlo -- cada uno de los dos CenfoBots necesita su propio config.py con
su propio MI_ARUCO_ID y PEER_MAC.

Pines confirmados en banco de pruebas (CircuitPython, IdeaBoard/ESP32 del kit
CenfoBot): ver docs/arquitectura.md y firmware/README.md para como se
verificaron. Los que siguen en "TODO" son especificos de la red/competencia,
no del hardware, y cambian cada vez que se prueba en un lugar distinto.
"""

# --- Identidad de este rover -------------------------------------------------
MI_ARUCO_ID = 10          # TODO: 10 u 11 segun el marcador fisico pegado al robot
COLOR_INICIAL = "green"   # color con el que arranca este rover (ver
                           # comun/protocolo_rovers.asignacion_estatica)

# --- Red (WiFi hacia el sistema de vision) -----------------------------------
WIFI_SSID = "TODO"
WIFI_PASSWORD = "TODO"
VISION_HOST = "TODO"      # IP de la PC que corre el sistema de vision (nunca 127.0.0.1)
VISION_PORT = 2026

# --- ESP-NOW (comunicacion directa rover<->rover, no pasa por el WiFi de arriba) --
# MAC (formato "AA:BB:CC:DD:EE:FF") del OTRO rover, no de este. Se obtiene
# imprimiendo wifi.radio.mac_address en cada robot -- OJO: verificar cual MAC
# corresponde a cual robot fisico justo antes de anotarla (por ejemplo
# comparando tambien microcontroller.cpu.uid), porque a simple vista las dos
# placas son identicas y es facil anotarlas cruzadas.
PEER_MAC = "TODO"
ESPNOW_CHANNEL = 6         # debe ser el mismo numero en los dos rovers

# --- Motores ------------------------------------------------------------------
# No llevan pines aca: firmware/motores.py usa la clase IdeaBoard (ib.motor_1 /
# ib.motor_2), que ya trae fijos de fabrica IO12/IO14 (motor_1) e IO13/IO15
# (motor_2). Confirmado en banco que ambos giran en las dos direcciones con el
# jumper SELECT-Vin puesto. Si "izquierda"/"derecha" salen invertidos en la
# calibracion, se corrige aca:
MOTOR_1_ES_IZQUIERDO = True   # TODO: confirmar una vez montados en el chasis

# --- Sensores infrarrojos (analogicos, 4x) -- pines confirmados en banco -----
PIN_IR_ADELANTE_IZQ = "IO36"
PIN_IR_ADELANTE_DER = "IO39"
PIN_IR_ATRAS_IZQ = "IO34"
PIN_IR_ATRAS_DER = "IO35"

# --- Sensor ultrasonico -- pines confirmados en banco (jumper SELECT-Vin puesto) --
PIN_ULTRASONICO_TRIG = "IO25"
PIN_ULTRASONICO_ECHO = "IO26"

# --- IMU (acelerometro/giroscopio, por el cable Qwiic/I2C) -------------------
# Confirmado en banco con un escaneo I2C: unico dispositivo encontrado fue el
# LSM6DS3TRC en 0x6B.
IMU_I2C_ADDR = 0x6B

# --- Sensor de luz/color (modulo VCC/DI/AO/GND, ver conexiones/sensorcolor2.png) --
# Este kit NO trae un chip de color por I2C: el escaneo de banco solo encontro
# el IMU (0x6B) en el bus Qwiic. El modulo de color es un NeoPixel (DI) +
# fototransistor analogico (AO). Solo sirve para detectar PRESENCIA (¿hay un
# cubo pegado al sensor?), no para distinguir de que color es -- ver
# firmware/sensores.py para el porque.
#
# OJO: el diagrama oficial del kit dice DI->IO32, AO->IO4, pero en banco el
# NeoPixel real resulto estar en IO33 en los DOS robots (no IO32) -- si se
# arma un tercer robot o se reemplaza esta placa, volver a verificar (prender
# blanco y mirar si el LED del modulo reacciona) antes de confiar en esto.
PIN_NEOPIXEL_COLOR = "IO33"   # confirmado en banco en ambos robots

# PIN_SENSOR_LUZ (AO) SI varia por robot -- no asumir el mismo valor en los dos:
#   - Robot en banco de COM6: IO4, confirmado y funcionando bien.
#   - Robot en banco de COM7: la placuita del modulo de color parece tener
#     defectos de hardware -- el canal VERDE del NeoPixel no enciende (se
#     probo visualmente, solo rojo y azul sirven), y el fototransistor (AO) no
#     dio una lectura util en ningun pin candidato (IO4, IO32, IO27), con o sin
#     WiFi activo. No es un problema de pin equivocado, parece la placuita
#     dañada o mal soldada -- revisar fisicamente / reemplazar el modulo antes
#     de confiar en `cubo_sujeto()` en ESE robot. Mientras tanto,
#     `PIN_SENSOR_LUZ = None` hace que `cubo_sujeto()` devuelva `False` de
#     forma segura (ver firmware/sensores.py) en vez de fallar.
PIN_SENSOR_LUZ = "IO4"        # TODO: poner None en el config.py del robot de
                               # COM7 hasta que se revise/cambie esa placuita
