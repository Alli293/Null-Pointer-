# Contrato de telemetría (resumen propio)

Resumen de trabajo del contrato publicado por el sistema de visión del reto. La fuente
de verdad es siempre `vision-system/contrato/CONTRATO.md` del repo guía
[Vision-Rover-Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge);
este documento es una referencia rápida para el equipo, no un reemplazo.

## Transporte

- TCP, puerto **2026**, NDJSON (un objeto JSON por línea, `\n`), UTF-8.
- El sistema de visión **solo publica**; el equipo nunca envía nada por este socket.
- ~20 Hz (una línea cada ~50ms).
- TCP no respeta límites de mensaje: hay que acumular en buffer y partir por `\n`
  (ver [`comun/mundo.py`](../comun/mundo.py) / `firmware/comm_vision.py`).

## Forma del mensaje

```json
{
  "v": 1, "seq": 123, "ts_ms": 1700000000000, "phase": "RUNNING",
  "grid": {"cols": 43, "rows": 43, "cell_mm": 20.0},
  "rovers": [{"id": 10, "col": 4.3, "row": 3.7, "theta": 46.2, "age_ms": 0}],
  "cubes": [{"color": "green", "col": 25.9, "row": 9.9, "age_ms": 0}],
  "obstacles": [],
  "start": {"col": 0.0, "row": 0.0},
  "depots": [{"color": "green", "col": 40.5, "row": 2.5}]
}
```

- `col`/`row`: celdas (float), 1 celda = 20mm. Origen `(0,0)` = esquina del marcador
  ArUco de menor ID.
- `theta`: grados, `0°` = derecha, sentido antihorario, rango `[0, 360]`.
- Cubos y depots se identifican por **`color`** (`red`/`green`/`blue`, máximo un cubo
  por color). Rovers por **`id`** (marcador ArUco montado en el robot).

## Reglas duras (no negociables)

1. **Buscar por identidad, nunca por posición en la lista.** Ni orden ni longitud de
   los arrays están garantizados.
2. **`age_ms` alto = oclusión, no desaparición.** El objeto sigue en la lista con su
   última posición conocida. Umbrales usados en este repo
   (`comun/contrato.py`): `< 200ms` fresco, `< 1500ms` dudoso, `>= 1500ms` no confiable.
3. **Quedarse solo con el último mensaje.** Es política de buffer único; huecos en
   `seq` son normales (mensajes perdidos), no hay que intentar recuperarlos.
4. **Vigilar latencia.** El contrato *no garantiza* sincronización de reloj entre la
   visión y el rover — por eso no restamos `ts_ms` contra un reloj de pared del robot
   directamente. Ver la nota de diseño abajo.
5. **Validar versión.** Si `v != 1`, descartar el mensaje (formato desconocido).

## Nota de diseño: por qué la latencia se mide como variación, no en absoluto

El contrato dice explícitamente que no garantiza reloj sincronizado entre la PC de
visión y el ESP32. Restar `ts_ms` (época Unix de la PC) contra el reloj del ESP32
(que normalmente ni siquiera corre en época Unix salvo que se sincronice por NTP)
daría un número sin sentido.

En vez de eso, `comun/mundo.py` (`EstimadorLatencia`) calcula, en la primera muestra,
un **offset base** = `ahora_local_ms - ts_ms`, y en cada muestra siguiente reporta
cuánto **creció** ese offset respecto a la base. Un crecimiento sostenido indica que
los mensajes están llegando cada vez más tarde (cola/latencia real), mientras que un
offset constante (aunque no sea cero) es solo el desfase de reloj, no un problema.
Esto es justamente "medir variación de latencia" en vez de latencia absoluta, tal
como sugiere el contrato en sus *non-guarantees*.

## Fases

`IDLE → READY → RUNNING → FINISHED → READY` (siguiente ronda). En `FINISHED` el rover
debe detenerse de inmediato sin importar en qué estado de su propia máquina de estados
esté (ver [`comun/maquina_estados.py`](../comun/maquina_estados.py)).
