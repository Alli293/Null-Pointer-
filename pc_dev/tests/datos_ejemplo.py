"""Frames de telemetria de ejemplo, escritos a mano siguiendo el schema del
contrato (ver docs/contrato_telemetria.md), para que los tests sean
deterministas sin depender de un publisher externo corriendo.
"""

GRID = {"cols": 43, "rows": 43, "cell_mm": 20.0}
DEPOTS = [
    {"color": "green", "col": 40.5, "row": 2.5},
    {"color": "red", "col": 2.5, "row": 40.5},
    {"color": "blue", "col": 40.5, "row": 40.5},
]
START = {"col": 0.0, "row": 0.0}


def _base(seq, phase="RUNNING", ts_ms=1_700_000_000_000, v=1):
    return {
        "v": v,
        "seq": seq,
        "ts_ms": ts_ms,
        "phase": phase,
        "grid": GRID,
        "rovers": [{"id": 10, "col": 4.3, "row": 3.7, "theta": 46.2, "age_ms": 0}],
        "cubes": [{"color": "green", "col": 5.0, "row": 4.0, "age_ms": 0}],
        "obstacles": [],
        "start": START,
        "depots": DEPOTS,
    }


# Mensaje normal: rover10 cerca de un cubo verde fresco.
MSG_NORMAL = _base(seq=1)

# Cubo verde ocluido (age_ms alto) -- sigue en la lista con su ultima posicion.
MSG_CUBO_OCLUIDO = _base(seq=2)
MSG_CUBO_OCLUIDO["cubes"] = [{"color": "green", "col": 5.0, "row": 4.0, "age_ms": 5000}]

# Cubo a distancia de agarre (< 1.0 celdas) del rover.
MSG_CUBO_CERCA = _base(seq=3)
MSG_CUBO_CERCA["cubes"] = [{"color": "green", "col": 4.5, "row": 3.9, "age_ms": 0}]

# Rover cerca del depot verde (col=40.5,row=2.5).
MSG_ROVER_EN_DEPOT = _base(seq=4)
MSG_ROVER_EN_DEPOT["rovers"] = [{"id": 10, "col": 40.2, "row": 2.6, "theta": 0, "age_ms": 0}]

# Ronda terminada.
MSG_FINISHED = _base(seq=5, phase="FINISHED")

# Version de protocolo desconocida -- debe descartarse.
MSG_VERSION_INVALIDA = _base(seq=6, v=2)

# Fase IDLE (antes de que arranque la ronda).
MSG_IDLE = _base(seq=7, phase="IDLE")
