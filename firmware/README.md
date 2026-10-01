# Firmware (CircuitPython, IdeaBoard ESP32)

Código que corre en cada CenfoBot (CRCibernetica IdeaBoard, CircuitPython 9.2.x). Importa la lógica de decisión de
[`comun/`](../comun/) sin modificarla. El contenido de fábrica de los rovers está respaldado en
[`rover_original/`](../rover_original/). El estado general del proyecto y el plan completo están en el
[README raíz](../README.md).

## Qué hay aquí

| Archivo | Para qué |
|---|---|
| `code.py` | Punto de entrada: se copia a la raíz del rover como `/code.py` y llama a `main.main()` |
| `main.py` | Loop: WiFi → telemetría de la visión → `ControladorRover.paso()` → motores + LED; frena si falla algo |
| `config.py` | Identidad por **MAC** (ID ArUco 10/11), pines, `PIN_LED`, `PIN_IR`, `FACTOR_VELOCIDAD` |
| `placa.py` | **Una sola** `IdeaBoard` para todo el firmware (una segunda instancia falla: "pin in use") |
| `motores.py` | `mover(izq, der)` en [-1, 1] (`motor_1` = izquierda, `motor_2` = derecha) |
| `sensores.py` | Ultrasónico HCSR04 (`cubo_sujeto`, `cubo_liberado_en_depot`); infrarrojo opcional |
| `indicador.py` | LED de estado (NeoPixel en **IO33**, GRB; ver la tabla de colores en el README raíz, §6) |
| `comm_vision.py` | Cliente TCP NDJSON de la visión (solo conserva el último mensaje) |
| `comm_espnow.py` | Mensajes entre rovers por ESP-NOW (probado, pero `main.py` aún no lo usa) |
| `settings.toml.example` | **Plantilla** de `/settings.toml` (WiFi y `VISION_HOST`) |

## Despliegue

Las librerías `ideaboard`, `hcsr04`, `adafruit_motor`, etc. ya vienen en `/lib` del rover. Guía completa (conexión,
respaldo, despliegue, pruebas) en el [README raíz](../README.md#5-cómo-nos-conectamos-a-los-rovers).

```bash
python herramientas/info_rover.py                       # identificar cada rover por UID (los COM cambian)
python herramientas/respaldar_rover.py COM12 rover1     # respaldo (solo lectura)
python herramientas/desplegar.py COM12                  # muestra qué copiaría
python herramientas/desplegar.py COM12 --si             # copia comun/ + firmware/ y REEMPLAZA /code.py
python herramientas/probar_led.py COM12                 # ver los estados del LED
```

**Credenciales:** crear `firmware/settings.toml` (Git lo ignora) **copiando** `settings.toml.example` y completando el
WiFi, la contraseña y `VISION_HOST` (IP de la PC de visión, de `ipconfig`). **Nunca escribir la contraseña en el
`.example`**: ese archivo se sube al repo. Después copiar el `settings.toml` al rover. Sin `VISION_HOST` el firmware
aborta con un mensaje y el LED queda rojo fijo, con los motores frenados.

Con el rover reiniciado, `python -m mpremote connect <PUERTO> repl` muestra los `print` (conexión y cambios de
estado). Cierra Thonny antes: no comparte el puerto. Si el cable se suelta durante el despliegue, **repetirlo completo**.

## Lo que falta en el firmware

Ver el [plan completo](../README.md#9-plan-completo-lo-que-falta-paso-a-paso). En corto: primera prueba de movimiento
con las ruedas en el aire, calibración (potencia mínima, velocidad, desvío, `DISTANCIA_AGARRE_CM`), rampa de
aceleración, ESP-NOW en `main.py`, sensor de color e IMU.

## Probar sin hardware

La lógica de decisión y el flujo de `main.py` (con hardware falso) se prueban con `pytest` en
[`pc_dev/`](../pc_dev/). Este directorio solo funciona en un dispositivo con CircuitPython.
