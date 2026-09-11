# Null-Pointer- — Vision Rover Challenge

Proyecto del equipo para el [Vision Rover Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge)
de Cenfotec: dos CenfoBot (ESP32) deben ubicar, transportar y depositar cubos de color
en su zona correspondiente, coordinándose entre sí, guiados por un sistema de visión
externo que **solo da percepción** (posiciones/orientación) — toda la estrategia y
decisión corre a bordo de los rovers, sin PC externa durante la ronda.

## Cómo se separa el repo

| Carpeta       | Dónde corre                | Qué contiene |
|---------------|-----------------------------|--------------|
| [`comun/`](comun/)       | **PC y ESP32** (mismo código) | Lógica de decisión pura: parseo/validación del contrato de telemetría, emparejamiento cubo↔depot, máquina de estados del rover. Un solo lugar de verdad para que la simulación en PC y el robot real nunca diverjan. |
| [`firmware/`](firmware/)   | Solo ESP32 (MicroPython)   | Lo que depende de hardware: motores, sensores, ESP-NOW, cliente TCP de visión. Importa `comun/`. |
| [`pc_dev/`](pc_dev/)     | Solo PC                    | Herramientas para iterar sin flashear ni tener el robot a mano: cliente de escritorio, runner de simulación, tests (`pytest`). |
| [`docs/`](docs/)       | —                           | Resumen propio del contrato de telemetría y decisiones de arquitectura. |
| [`simulacion/`](simulacion/) | —                       | Cómo levantar el publisher simulado del repo guía para probar en vivo sin hardware. |

La idea central: la lógica de decisión (`comun/`) se escribe una sola vez, en un
subconjunto de Python compatible con CPython y MicroPython, se prueba con `pytest`
en la PC, y se copia **sin cambios** al ESP32. Así lo que se validó en simulación es
literalmente lo que corre en el robot.

## Quickstart

```bash
# 1. Instalar dependencias de PC (solo pytest — el cliente usa socket/json de la librería estándar)
pip install -r pc_dev/requirements.txt

# 2. Correr los tests de la lógica de decisión (sin hardware, sin red)
cd pc_dev
pytest

# 3. Probar contra telemetría simulada (ver simulacion/README.md para levantar el publisher)
python ejecutar_simulacion.py --host 127.0.0.1 --port 2026 --id 10 --color green
```

Para flashear el firmware a un CenfoBot, ver [`firmware/README.md`](firmware/README.md).

## Referencias

- Repo guía del reto (reglas, specs del robot, sistema de visión): [Vision-Rover-Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge)
- Detalle del protocolo de telemetría (resumen propio): [`docs/contrato_telemetria.md`](docs/contrato_telemetria.md)
- Decisiones de arquitectura y diagrama de capas: [`docs/arquitectura.md`](docs/arquitectura.md)
