# Firmware (CircuitPython, ESP32 / CRCibernetica IdeaBoard)

Código que corre físicamente en cada CenfoBot. Importa la lógica de decisión
de [`comun/`](../comun/) sin modificarla.

## CircuitPython, no MicroPython

El kit CenfoBot trae de fábrica **CircuitPython** sobre la IdeaBoard (confirmado
en banco: `Adafruit CircuitPython 9.2.4 ... CRCibernetica IdeaBoard with ESP32`),
no MicroPython genérico. Por eso este firmware usa las librerías de
CircuitPython (`wifi`, `socketpool`, `espnow`, `analogio`, la clase `IdeaBoard`
del repo guía) en vez de los módulos equivalentes de MicroPython (`network`,
`socket`, `machine`).

Ese ESP32 (con chip USB-serial **CH340** externo) **no tiene USB nativo**, así
que nunca va a aparecer como unidad `CIRCUITPY` en el explorador de archivos —
eso es normal, no un fallo. Se interactúa por consola serie (REPL).

## Qué ya quedó confirmado en banco de pruebas

- **Motores**: `ib.motor_1` (IO12/IO14) e `ib.motor_2` (IO13/IO15) de la clase
  `IdeaBoard`, jumper SELECT↔Vin puesto en el driver, alimentados por la
  batería del robot (el USB del PC solo no alcanza).
- **LED/NeoPixel, IMU** (LSM6DS3TRC en `0x6B` por I2C/Qwiic).
- **Sensores IR** (`IO36`/`IO39`/`IO34`/`IO35`) y **ultrasónico**
  (`TRIG=IO25`, `ECHO=IO26`, mismo jumper SELECT↔Vin).
- **WiFi** hacia el sistema de visión: `wifi.radio.connect(...)` +
  `socketpool.SocketPool` recibiendo NDJSON real del simulador.
- **ESP-NOW** entre los dos robots, en ambas direcciones (`espnow` nativo de
  CircuitPython + el truco `start_ap()`/`stop_ap()` para fijar canal sin
  asociarse a ningún WiFi real).

Ver [`docs/arquitectura.md`](../docs/arquitectura.md) para el detalle.

## Qué falta antes de correr esto en la ronda real

- **Sensor de color** (`firmware/sensores.py: leer_color()`): este kit no
  trae un chip de color por I2C — el escaneo de banco solo encontró el IMU.
  Va por luz analógica + NeoPixel (`codigos/color_detect.py` del
  [repo guía](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge)),
  y necesita calibración (`MIN_LUZ`/`MAX_LUZ`) propia de cada robot.
- **Calibración de motores** (`motores.py: _factor_izq/_factor_der`) — adaptar
  `codigos/motor_calibration.py`.
- **Control de rumbo con PID** (`movimiento.py`) — hoy es bang-bang simple;
  adaptar `codigos/code_PID.py`, `codigos/move_heading.py`, `codigos/turn_angle.py`.
- **`config.py` por robot**: `MI_ARUCO_ID`, `PEER_MAC`, `WIFI_SSID/PASSWORD`,
  `VISION_HOST` son específicos de cada robot y de la red del día — no vienen
  cargados. Ver advertencia sobre `PEER_MAC` abajo.

## Copiar el código al robot (sin unidad CIRCUITPY)

No hay drag-and-drop porque este ESP32 no expone almacenamiento USB. Usar
**Thonny**:

1. Conectar el robot por USB. En Device Manager debería aparecer
   `USB-SERIAL CH340 (COMx)`.
2. Abrir Thonny → Herramientas → Opciones → Intérprete → **"CircuitPython
   (generic)"** y el puerto `COMx` correspondiente.
3. Con el panel `View → Files` abierto, copiar a la raíz del dispositivo:
   - la carpeta [`comun/`](../comun/) completa,
   - la carpeta `firmware/` completa,
   - `boot.py`,
   - y como `code.py` en la raíz, un script mínimo que haga
     `from firmware.main import main; main()` (o copiar `firmware/main.py`
     como `code.py` directamente).
4. Editar **`firmware/config.py` en el dispositivo** (o antes de copiar) con
   los valores de ese robot específico — cada uno de los dos necesita su
   propio `config.py`.
5. Reiniciar el ESP32 (botón físico o `Ctrl-D` en la consola de Thonny);
   `code.py`/`main.py` arranca solo.

### Librerías de CircuitPython que hacen falta en `/lib`

Además del código propio, el robot necesita en su carpeta `/lib` (Adafruit
CircuitPython Bundle, o copiadas del repo guía):

- `ideaboard.py` (del repo guía — driver de la placa, motores/NeoPixel).
- `adafruit_motor/` (usada por `ideaboard.py`).
- `adafruit_lsm6ds/` (IMU).
- `neopixel.py`, `simpleio.py`, `rainbowio.py` (dependencias de `ideaboard.py`).
- `hcsr04.py` (sensor ultrasónico).

### ⚠️ `PEER_MAC`: verificar cuál MAC es cuál robot

Las dos placas son físicamente idénticas. En banco nos pasó que las MACs
anotadas durante la prueba de WiFi quedaron cruzadas respecto a qué robot era
cuál, y el ESP-NOW no funcionaba hasta corregirlo. Antes de anotar un
`PEER_MAC`, confirmar en la consola de **ese mismo robot**:

```python
import wifi, microcontroller
print("UID:", [hex(b) for b in microcontroller.cpu.uid])
print("MAC:", ":".join("{:02X}".format(b) for b in wifi.radio.mac_address))
```

y anotar la MAC en el `config.py` del **otro** robot, no del mismo.

## Antes de esto: probar sin hardware

Toda la lógica de decisión (`comun/`) y el ciclo completo se pueden probar sin
ningún ESP32 usando [`pc_dev/`](../pc_dev/) — ver el README raíz y
[`simulacion/README.md`](../simulacion/README.md). Solo lo que es
genuinamente específico de hardware (motores, sensores, ESP-NOW) necesita el
robot físico.
