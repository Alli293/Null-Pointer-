# Firmware (CircuitPython, IdeaBoard ESP32)

Código que corre en cada CenfoBot (CRCibernetica IdeaBoard, CircuitPython 9.2.x).
Importa la lógica de decisión de [`comun/`](../comun/) sin modificarla.
El código de fábrica que traían los rovers está respaldado en [`rover_original/`](../rover_original/).

## Qué falta (TODO) antes de correr en el robot completo

- `config.py`: `VISION_HOST` (IP de la PC de visión). ID y MAC de cada rover ya se autodetectan por MAC.
- Calibración de motores (`motores.py`, factores por motor).
- Sensor de agarre: hoy es solo el ultrasónico (`sensores.py`); calibrar `DISTANCIA_AGARRE_CM`.
- Calibrar con el robot real los números de `comun/planificador.py` y la velocidad/giro de los motores (el control actual es proporcional de rumbo, sin PID).
- Negociación robusta rover↔rover (`comun/protocolo_rovers.py`).

## Despliegue

Las librerías `ideaboard`, `hcsr04`, `adafruit_motor`, etc. ya vienen en `/lib` del rover.
Guía completa (conexión, respaldo, despliegue, pruebas) en el [README raíz](../README.md#4-cómo-nos-conectamos-a-los-rovers).

```bash
python herramientas/respaldar_rover.py COM3 rover1     # respaldo (solo lectura)
python herramientas/desplegar.py COM3                   # muestra qué copiaría
python herramientas/desplegar.py COM3 --si              # copia comun/ + firmware/ y REEMPLAZA /code.py
```

Copiar además `settings.toml.example` al rover como `/settings.toml` (con el WiFi y `VISION_HOST`
reales; NO se sube al repo). Sin `VISION_HOST` el firmware aborta con un mensaje y deja los
motores frenados. Con el rover reiniciado, `python -m mpremote connect <PUERTO> repl` muestra los
`print` (conexión y cambios de estado). Cierra Thonny antes: no comparte el puerto.

## Probar sin hardware

La lógica de decisión se prueba con `pytest` en [`pc_dev/`](../pc_dev/).
Este directorio solo compila en un dispositivo con CircuitPython.
