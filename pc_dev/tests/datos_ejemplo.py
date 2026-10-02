"""Frames de telemetria de ejemplo, escritos a mano siguiendo el schema del
contrato **v2** (ver docs/contrato_telemetria.md), para que los tests sean
deterministas sin depender de un publisher externo corriendo.
"""

GRID = {"cols": 43, "rows": 43, "cell_mm": 20.0}
DEPOT_SIZE = {"length": 10.0, "depth": 7.5}
CUBE_SIDE = 3.0
DEPOTS = [
    {"color": "green", "col": 21.5, "row": 3.75},
    {"color": "red", "col": 39.25, "row": 21.5},
    {"color": "blue", "col": 21.5, "row": 39.25},
]
START = {"col": 3.75, "row": 21.5}  # v2: ya NO coincide con el origen (0,0)


def _base(seq, phase="RUNNING", ts_ms=1_700_000_000_000, v=2, remaining_ms=500_000):
    return {
        "v": v,
        "seq": seq,
        "ts_ms": ts_ms,
        "phase": phase,
        "clock": {"elapsed_ms": 600_000 - remaining_ms, "remaining_ms": remaining_ms, "total_ms": 600_000},
        "grid": GRID,
        "rovers": [{"id": 10, "col": 4.3, "row": 3.7, "theta": 46.2, "age_ms": 0}],
        "cubes": [{"color": "green", "col": 5.0, "row": 4.0, "age_ms": 0}],
        "obstacles": [],
        "start": START,
        "depots": DEPOTS,
        "depot_size": DEPOT_SIZE,
        "cube_side": CUBE_SIDE,
    }


# Mensaje normal: rover10 cerca de un cubo verde fresco.
MSG_NORMAL = _base(seq=1)

# Cubo verde ocluido (age_ms alto) -- sigue en la lista con su ultima posicion.
MSG_CUBO_OCLUIDO = _base(seq=2)
MSG_CUBO_OCLUIDO["cubes"] = [{"color": "green", "col": 5.0, "row": 4.0, "age_ms": 5000}]

# Cubo a distancia de agarre (< 1.0 celdas) del rover.
MSG_CUBO_CERCA = _base(seq=3)
MSG_CUBO_CERCA["cubes"] = [{"color": "green", "col": 4.5, "row": 3.9, "age_ms": 0}]

# Rover cerca del depot verde (centro en col=21.5,row=3.75) -- suficiente para
# disparar la transicion TRANSPORTAR -> ENTREGAR (umbral de aproximacion), pero
# el cubo (ver mas abajo) puede seguir estando lejos de estar REALMENTE entregado.
MSG_ROVER_EN_DEPOT = _base(seq=4)
MSG_ROVER_EN_DEPOT["rovers"] = [{"id": 10, "col": 21.2, "row": 3.6, "theta": 0, "age_ms": 0}]
MSG_ROVER_EN_DEPOT["cubes"] = [{"color": "green", "col": 26.0, "row": 10.0, "age_ms": 0}]  # lejos del depot todavia

# Cubo verde YA colocado exactamente en el centro de su zona -- cubo_en_su_zona
# debe dar (True, 0.0), igual que el ejemplo de la seccion 2 del contrato.
MSG_CUBO_ENTREGADO = _base(seq=5)
MSG_CUBO_ENTREGADO["rovers"] = [{"id": 10, "col": 21.2, "row": 3.6, "theta": 0, "age_ms": 0}]
MSG_CUBO_ENTREGADO["cubes"] = [{"color": "green", "col": 21.5, "row": 3.75, "age_ms": 0}]

# Ronda terminada.
MSG_FINISHED = _base(seq=6, phase="FINISHED", remaining_ms=0)

# Version de protocolo desconocida (la v1 vieja) -- debe descartarse.
MSG_VERSION_INVALIDA = _base(seq=7, v=1)

# Fase IDLE (antes de que arranque la ronda).
MSG_IDLE = _base(seq=8, phase="IDLE", remaining_ms=0)
