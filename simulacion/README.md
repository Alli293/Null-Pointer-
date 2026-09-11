# Simulación (sin hardware)

Cómo probar todo el pipeline de decisión (`comun/` + `pc_dev/`) contra telemetría
simulada, sin tener el robot ni el sistema de visión real a mano.

## 1. Levantar el publisher simulado

El repo guía trae un simulador con ruido, oclusiones y movimiento realista:
[`vision-system/contrato/mock_publisher.py`](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge/blob/main/vision-system/contrato/mock_publisher.py).
No se copia a este repo (es código de otro repo/organización) — se clona aparte:

```bash
git clone https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge.git ../Vision-Rover-Challenge
cd ../Vision-Rover-Challenge/vision-system/contrato
pip install -r requirements.txt
python mock_publisher.py
```

Esto deja un servidor NDJSON escuchando en `127.0.0.1:2026`, publicando rovers,
cubos y depots simulados a 20Hz — el mismo formato que el sistema de visión real
(ver [`docs/contrato_telemetria.md`](../docs/contrato_telemetria.md)).

`config_simulador.json` (en esa misma carpeta del repo guía) permite ajustar
cantidad de cubos, ruido, oclusiones, etc. — útil para forzar escenarios como
"cubo ocluido" o "latencia alta" y ver cómo reacciona la máquina de estados.

## 2. Correr nuestra simulación contra ese publisher

Desde este repo:

```bash
cd pc_dev
python ejecutar_simulacion.py --host 127.0.0.1 --port 2026 --id 10 --color green
```

Imprime cada cambio de estado del `RoverFSM` y, cada cierto número de frames, el
mundo visto (posición propia, cubo del color asignado, si el mensaje se considera
"utilizable"). Sirve para confirmar en vivo que:

- El emparejamiento por `color`/`id` funciona con datos que van cambiando.
- Las transiciones de estado ocurren cuando deberían (acercamiento, oclusión, `FINISHED`).
- El corte por versión/latencia no se dispara falsamente con tráfico normal.

## Qué NO cubre esta simulación

- Nada de motores/sensores reales (eso es `firmware/`, solo se prueba en banco físico).
- La coordinación entre los dos rovers vía ESP-NOW (hoy es un placeholder en
  `comun/protocolo_rovers.py`) — para probarla habría que correr dos instancias
  de `ejecutar_simulacion.py` en paralelo y, más adelante, un mecanismo de mensajes
  compartido que simule ESP-NOW en la PC.
