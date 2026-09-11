"""Formato de mensaje inter-rover (via ESP-NOW) y una asignacion de colores
minima para arrancar.

TODO (siguiente iteracion, no de este esqueleto): negociacion robusta de
"quien va por que cubo" tolerante a mensajes ESP-NOW perdidos -- hoy la
asignacion es estatica (round-robin por id de rover) y no hay reclamo/liberacion
en vivo. Esto cubre el caso feliz para poder simular y probar movimiento; la
anti-colision real ("Collision Avoidance" / "Imperfect Information Handling" del
el_reto.md del repo guia) queda pendiente.
"""

from comun import contrato

# Tipos de mensaje inter-rover.
MSG_RECLAMAR = "RECLAMAR"   # "voy a ir por este color"
MSG_LIBERAR = "LIBERAR"     # "ya no voy por este color" (entregado o abandonado)
MSG_POSICION = "POSICION"   # broadcast periodico de posicion propia (redundante a
                             # la vision, util si un rover pierde la señal de vision)


def construir_mensaje(tipo, rover_id, color=None, col=None, row=None):
    """Arma el dict que se serializa y se manda por ESP-NOW al otro rover."""
    msg = {"tipo": tipo, "rover_id": rover_id}
    if color is not None:
        msg["color"] = color
    if col is not None and row is not None:
        msg["col"] = col
        msg["row"] = row
    return msg


def asignacion_estatica(ids_rovers, colores=contrato.COLORES):
    """Reparto simple y determinista de colores entre rovers, sin comunicacion.

    Sirve como fallback de arranque y para simular con un solo rover en pc_dev/.
    Con 2 rovers y 3 colores, un rover queda con 2 colores en cola (se le asignan
    en orden; el segundo se activa cuando el FSM llega a OCIOSO con el primero).

    Devuelve {rover_id: [colores...]}.
    """
    ids_ordenados = sorted(ids_rovers)
    reparto = {rid: [] for rid in ids_ordenados}
    for i, color in enumerate(colores):
        rid = ids_ordenados[i % len(ids_ordenados)]
        reparto[rid].append(color)
    return reparto
