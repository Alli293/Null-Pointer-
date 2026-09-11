# Firmware (MicroPython, ESP32)

Código que corre físicamente en cada CenfoBot. Importa la lógica de decisión
de [`comun/`](../comun/) sin modificarla.

## Qué falta antes de correr esto en un robot real

Todo lo marcado `TODO` en este directorio depende de tener el robot en banco:

- Pines de motor/sensores en [`config.py`](config.py) — confirmar contra
  `conexiones/README.md` y `robot.md` del [repo guía](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge).
- Calibración de motores (`motores.py`) — adaptar `codigos/motor_calibration.py`.
- Conexión WiFi y ESP-NOW reales (`main.py: conectar_wifi()`, `comm_espnow.py`).
- Control de rumbo con PID (`movimiento.py`) — adaptar `codigos/code_PID.py`,
  `codigos/move_heading.py`, `codigos/turn_angle.py`.

## Flasheo (una vez el firmware esté listo para probar)

1. Instalar MicroPython en el ESP32 (una sola vez, con `esptool`):
   ```bash
   pip install esptool mpremote
   esptool.py --chip esp32 erase_flash
   esptool.py --chip esp32 write_flash -z 0x1000 <firmware-micropython.bin>
   ```
2. Copiar el código al dispositivo con `mpremote` (o `ampy`, o Thonny si se
   prefiere GUI):
   ```bash
   mpremote connect <PUERTO> fs cp -r ../comun :comun
   mpremote connect <PUERTO> fs cp -r . :firmware
   mpremote connect <PUERTO> fs cp boot.py :boot.py
   ```
3. Editar `config.py` **en el dispositivo** (o antes de copiar) con el `MI_ARUCO_ID`,
   credenciales WiFi e IP de la PC de visión correctos para ese rover específico —
   cada uno de los dos robots necesita su propio `config.py`.
4. Reiniciar el ESP32; `main.py` arranca solo.

## Antes de esto: probar sin hardware

Toda la lógica de decisión (`comun/`) y el ciclo completo se pueden probar sin
ningún ESP32 usando [`pc_dev/`](../pc_dev/) — ver el README raíz y
[`simulacion/README.md`](../simulacion/README.md). Solo lo que es
genuinamente específico de hardware (motores, sensores, ESP-NOW) necesita el
robot físico.
