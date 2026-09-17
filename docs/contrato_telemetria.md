# Contrato de telemetría (resumen propio) — protocolo v2

Resumen de trabajo del contrato publicado por el sistema de visión del reto. La fuente
de verdad es siempre `vision-system/contrato/CONTRATO.md` del repo guía
[Vision-Rover-Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge);
este documento es una referencia rápida para el equipo, no un reemplazo.

> **El repo guía subió de v1 a v2** (sep-2026). Si algo de este documento no
> coincide con `CONTRATO.md` del repo guía, ese manda — este resumen puede
> haber quedado atrás.

## Transporte

- TCP, puerto **2026**, NDJSON (un objeto JSON por línea, `\n`), UTF-8.
- El sistema de visión **solo publica**; el equipo nunca envía nada por este socket.
- ~20 Hz (una línea cada ~50ms).
- TCP no respeta límites de mensaje: hay que acumular en buffer y partir por `\n`
  (ver `comun/mundo.py` / `firmware/comm_vision.py`).

## Forma del mensaje (v2)

```json
{
  "v": 2, "seq": 4137, "ts_ms": 1785012345678, "phase": "RUNNING",
  "clock": {"elapsed_ms": 88000, "remaining_ms": 512000, "total_ms": 600000},
  "grid": {"cols": 43, "rows": 43, "cell_mm": 20.0},
  "rovers": [{"id": 10, "col": 18.4, "row": 6.7, "theta": 84.2, "age_ms": 0}],
  "cubes": [{"color": "green", "col": 21.48, "row": 3.76, "age_ms": 0}],
  "obstacles": [],
  "start": {"col": 3.75, "row": 21.5},
  "depots": [{"color": "green", "col": 21.5, "row": 3.75}],
  "depot_size": {"length": 10.0, "depth": 7.5},
  "cube_side": 3.0
}
```

- `col`/`row`: celdas (float), 1 celda = 20mm.
- `theta`: grados, `0°` = derecha, sentido antihorario, rango `[0, 360]`.
- Cubos y depots se identifican por **`color`** (`red`/`green`/`blue`, máximo un cubo
  por color). Rovers por **`id`** (marcador ArUco montado en el robot).

## Qué cambió en v2 (respecto a v1, que es lo que documentamos originalmente)

1. **`v` ahora vale `2`.** `comun/contrato.py: VERSION_SOPORTADA = 2`. Un mensaje
   con otro valor se descarta sin intentar interpretarlo.
2. **`clock` (nuevo, raíz del mensaje):** el reloj **oficial** de la ronda
   (`elapsed_ms`, `remaining_ms`, `total_ms`), del mismo instante que `ts_ms`.
   **No llevar cronómetro propio** — se desincroniza. Usar
   `mundo.tiempo_restante_ms(msg)`.
3. **`depot_size` y `cube_side` (nuevos, raíz del mensaje):** tamaño de las
   zonas de entrega (`{length, depth}`, en celdas) y lado del cubo (en celdas).
   Con esto se puede calcular la condición de entrega **exacta** en vez de
   estimarla — ver más abajo.
4. **`start` ya NO es el origen.** Hasta v1, `start` coincidía con `(0,0)`
   (el marcador ArUco de menor ID). En v2, `start` es el punto de salida real
   de los robots (centro del lado izquierdo de la cancha) y el origen sigue
   siendo el marcador 0 — son dos cosas distintas ahora. Nuestro código no
   usaba `start` como origen en ningún lado, así que esto no rompió nada,
   pero hay que tenerlo presente si se agrega lógica que dependa de `start`.
5. **Las zonas de entrega (`depots[]`) son rectángulos, no puntos.** `col`/`row`
   siguen siendo el emparejamiento por `color`, pero ahora representan el
   **centro** de un rectángulo de `depot_size` celdas, no un punto de destino
   aproximado.

## Cuándo un cubo está realmente entregado (v2)

Ya no alcanza con acercar el rover al depot. El reglamento exige que el cubo
quede **completamente dentro** del rectángulo de su zona, con cualquier
rotación. La fórmula exacta (la misma que usa el sistema de visión para dar
el veredicto oficial) está implementada en `comun/mundo.cubo_en_su_zona()`,
copiada tal cual del contrato:

1. Se determina sobre qué borde de la cancha apoya la zona (el más cercano a
   su centro).
2. Se calcula el margen de media diagonal del cubo (`cube_side * √2 / 2`):
   el radio que garantiza que el cubo entra completo sin importar su rotación
   (que no viaja en el mensaje, así que no hace falta conocerla).
3. Se compara el centro del cubo contra la "ventana de aceptación" resultante.

`comun/maquina_estados.py` usa esta función para decidir la transición
`ENTREGAR → OCIOSO`: a diferencia del **agarre** (que la visión no puede
verificar — un cubo cerca del rover se ve igual esté sujeto o no), la
**entrega sí es verificable por visión**, porque una vez soltado el cubo se
asienta en una posición que la cámara puede comparar contra la zona. Por eso
`RoverFSM.transicion()` sale de `ENTREGAR` con lo que reporta la visión,
sin depender de que el firmware acierte un sensor.

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
5. **Validar versión.** Si `v != 2`, descartar el mensaje (formato desconocido).

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
Esto es justamente "medir variación de latencia", tal como sugiere el contrato
en la sección 6.4 cuando los relojes difieren mucho.

## Fases

`IDLE → READY → RUNNING → FINISHED → READY` (siguiente ronda). `READY → RUNNING`
la dispara **el reloj oficial solo** (no hay comando para adelantarla). En
`FINISHED` el rover debe detenerse de inmediato sin importar en qué estado de
su propia máquina de estados esté (ver `comun/maquina_estados.py`).
