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
   │  comun/  — lógica de decisión pura (CPython y CircuitPython)        │
   │    contrato.py         constantes + validación del mensaje        │
   │    mundo.py            emparejar por identidad, frescura, latencia│
   │    maquina_estados.py  RoverFSM: qué hacer según el mundo         │
   │    protocolo_rovers.py formato de mensaje inter-rover             │
   │    navegacion.py       geometria + control de rumbo (puro)        │
   │    planificador.py     a donde ir segun el estado (puro)          │
   │    rover.py            ControladorRover: FSM+planificador+colores │
   └───────────┬───────────────────────────────────────┬───────────────┘
               │ corre en                              │ corre en
               ▼                                        ▼
   ┌───────────────────────────┐            ┌─────────────────────────────┐
   │  pc_dev/ (solo PC)        │            │  firmware/ (solo ESP32)     │
   │  cliente de escritorio    │            │  comm_vision.py (TCP real)  │
   │  + ejecutar_simulacion.py │            │  comm_espnow.py (rover↔rover)│
   │  + tests (pytest)         │            │  motores.py / sensores.py   │
   │                           │            │  sensores.py                │
   └───────────────────────────┘            └─────────────────────────────┘
```

`comun/` no importa nada de `firmware/` ni de `pc_dev/`, y no usa ninguna librería que
no exista en CircuitPython (nada de `dataclasses`, `typing` en tiempo de ejecución,
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

## Lazo de control y simulación

`comun/rover.py: ControladorRover.paso(msg, tiene_cubo)` recibe telemetría y devuelve
`(izq, der)` para las ruedas. Lo usan igual `firmware/main.py` y el simulador físico
`pc_dev/simulador_fisico.py`, que cierra el lazo (mueve rovers, empuja cubos, genera
telemetría v2). `pytest` verifica que los dos rovers entregan los 3 cubos (~30 s
simulados, sin choques; también con ruido de visión).

Estrategia: el cubo se **empuja** con el frente (entre las paletas). El rover se ubica
detrás del cubo (lado opuesto al depot), avanza siguiendo la línea cubo→depot y suelta
cuando la visión confirma el cubo adentro de la zona (con 1 celda de margen); luego
retrocede. Si el cubo se escapa, vuelve a recuperarlo.

## Qué queda pendiente

- **Coordinación real entre los dos rovers** (`comun/protocolo_rovers.py`): hoy el
  reparto de colores es estático (por id) y la evitación de colisiones es una regla
  simple de cesión de paso (el id mayor cede) — con ruido de visión alto quedan
  roces ocasionales. Falta la negociación robusta ante mensajes ESP-NOW perdidos,
  reasignación dinámica (que un rover ayude al otro) y evitación real. Es la parte
  más delicada del reto ("Imperfect Information Handling" + "Collision Avoidance").
- **Calibración con el robot real**: los números de `planificador.py` (celdas,
  velocidades), `DISTANCIA_AGARRE_CM`, y la velocidad/giro reales de los motores
  (el simulador asume 6 celdas/s y 90°/s a potencia máxima).
- **Sensor de agarre real**: hoy es el ultrasónico; reforzar con el sensor de color.
