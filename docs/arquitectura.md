# Arquitectura

## Capas

```
                 ┌─────────────────────────────────────────┐
                 │   Sistema de visión (externo, fijo)      │
                 │   TCP:2026 NDJSON, 20Hz — solo percepción│
                 └───────────────┬───────────────────────────┘
                                 │ telemetría (rovers, cubes, depots, phase)
                                 ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  comun/  — lógica de decisión pura (CPython y MicroPython)        │
   │    contrato.py         constantes + validación del mensaje        │
   │    mundo.py            emparejar por identidad, frescura, latencia│
   │    maquina_estados.py  RoverFSM: qué hacer según el mundo         │
   │    protocolo_rovers.py formato de mensaje inter-rover             │
   └───────────┬───────────────────────────────────────┬───────────────┘
               │ corre en                              │ corre en
               ▼                                        ▼
   ┌───────────────────────────┐            ┌─────────────────────────────┐
   │  pc_dev/ (solo PC)        │            │  firmware/ (solo ESP32)     │
   │  cliente de escritorio    │            │  comm_vision.py (TCP real)  │
   │  + ejecutar_simulacion.py │            │  comm_espnow.py (rover↔rover)│
   │  + tests (pytest)         │            │  motores.py / movimiento.py │
   │                           │            │  sensores.py                │
   └───────────────────────────┘            └─────────────────────────────┘
```

`comun/` no importa nada de `firmware/` ni de `pc_dev/`, y no usa ninguna librería que
no exista en MicroPython (nada de `dataclasses`, `typing` en tiempo de ejecución,
`enum`, etc. — solo `dict`/`list`/constantes simples). Eso es lo que permite probarlo
con `pytest` en la PC y copiarlo tal cual al robot.

## Máquina de estados de un rover (`comun/maquina_estados.py`)

```
   BUSCAR ──(cubo asignado fresco)──▶ APROXIMAR
     ▲                                    │
     │ (cubo se vuelve no confiable)      │ (distancia < umbral de agarre)
     └────────────────────────────────────┤
                                            ▼
                                        SUJETAR ──(sensor confirma agarre)──▶ TRANSPORTAR
                                                                                   │
                                                                    (distancia a depot < umbral)
                                                                                   ▼
                             OCIOSO ◀──(sensor O vision confirman entrega)── ENTREGAR

   cualquier estado ──(phase == FINISHED)──▶ DETENIDO
```

Puntos importantes:
- El **agarre** no se puede decidir con telemetría de visión (esa da posición, no
  contacto físico: un cubo cerca del rover se ve igual este sujeto o no). Se
  confirma con sensores del propio rover (color/IR/switch) y se pasa a
  `RoverFSM.transicion(...)` como parámetro explícito (`tiene_cubo`) — así
  `comun/` no depende de qué sensor exacto usa el firmware.
- La **entrega**, en cambio, sí es verificable por visión desde el protocolo v2:
  una vez soltado, el cubo se asienta en una posición que la cámara reporta, y
  `depot_size`/`cube_side` alcanzan para calcular con la fórmula exacta del
  contrato si quedó completamente dentro de su zona
  (`comun/mundo.cubo_en_su_zona`). Por eso `ENTREGAR → OCIOSO` sale con lo que
  ve la visión, y `cubo_entregado` (señal del sensor) queda como confirmación
  adicional/redundante, no como único camino.
- `OCIOSO` es un estado a la espera de una nueva asignación de color (ver
  `protocolo_rovers.py`), no necesariamente el fin de la ronda.
- `DETENIDO` (por `FINISHED`) tiene prioridad sobre cualquier otra transición.

## Qué queda pendiente para la siguiente iteración

- **Coordinación real entre los dos rovers** (`comun/protocolo_rovers.py`): el
  esqueleto trae una asignación estática simple (reparto de colores por índice) y el
  formato de mensaje para reclamar/liberar un color por ESP-NOW, pero no la
  negociación robusta ante mensajes perdidos (es la parte más delicada del reto:
  "Imperfect Information Handling" + "Collision Avoidance" del `el_reto.md` del repo
  guía).
- **Geometría fina de acercamiento/agarre** (orientación relativa, evasión de
  obstáculos, corrección con PID) — vive en `firmware/movimiento.py`, fuera de
  `comun/` a propósito porque depende de las paletas/sensores físicos del kit.
- **Pines y calibración de motores** — quedan como `TODO` explícitos en
  `firmware/config.py` hasta tener el robot en banco.
