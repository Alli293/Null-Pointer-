# Firmware (CircuitPython, IdeaBoard ESP32)

Código que corre en cada CenfoBot (CRCibernetica IdeaBoard, CircuitPython 9.2.x).
Importa la lógica de decisión de [`comun/`](../comun/) sin modificarla.
El código de fábrica que traían los rovers está respaldado en [`rover_original/`](../rover_original/).

## Qué falta (TODO) antes de correr en el robot completo

- `config.py`: `VISION_HOST` (IP de la PC de visión); ID, color y MAC de cada rover ya se autodetectan por MAC.
- Calibración de motores (`motores.py`, factores por motor).
- Sensor de agarre: hoy es solo el ultrasónico (`sensores.py`); calibrar `DISTANCIA_AGARRE_CM`.
- Control de rumbo con PID (`movimiento.py`) y maniobra de agarre/entrega.
- Negociación robusta rover↔rover (`comun/protocolo_rovers.py`).

## Despliegue

Las librerías `ideaboard`, `hcsr04`, `adafruit_motor`, etc. ya vienen en `/lib` del rover.

```bash
pip install mpremote
mpremote connect <PUERTO> fs cp -r ../comun :comun
mpremote connect <PUERTO> fs cp -r . :firmware
mpremote connect <PUERTO> fs cp code.py :code.py     # OJO: reemplaza el code.py de prueba
```

Crear en la raíz del dispositivo un `settings.toml` (NO se sube al repo):

```toml
CIRCUITPY_WIFI_SSID = "..."
CIRCUITPY_WIFI_PASSWORD = "..."
```

El mismo `config.py` sirve para los dos rovers (se identifican por MAC).
Cierra Thonny antes de usar `mpremote`: ambos no pueden compartir el puerto.

## Probar sin hardware

La lógica de decisión se prueba con `pytest` en [`pc_dev/`](../pc_dev/).
Este directorio solo compila en un dispositivo con CircuitPython.
