"""Geometria y control de movimiento puros (sin hardware).

Convenciones (las mismas de la telemetria, ver docs/contrato_telemetria.md):
- col crece hacia la derecha, row crece hacia ABAJO.
- theta en grados, 0 = hacia col creciente, sentido antihorario (visto en pantalla).
- Comando de rueda en [-1, 1]; w > 0 = giro antihorario (la rueda derecha gana).

Solo usa math: corre igual en CPython y CircuitPython.
"""

from math import atan2, cos, degrees, radians, sqrt


def normalizar_180(angulo):
    """Lleva un angulo en grados a [-180, 180)."""
    return (angulo + 180.0) % 360.0 - 180.0


def rumbo_de_vector(dcol, drow):
    """Angulo theta (grados, [0, 360)) de un vector (dcol, drow) en coordenadas
    de cancha (row hacia abajo)."""
    return degrees(atan2(-drow, dcol)) % 360.0


def rumbo_hacia(origen, destino):
    """Theta desde `origen` hacia `destino` (objetos con col/row)."""
    return rumbo_de_vector(destino["col"] - origen["col"], destino["row"] - origen["row"])


def unitario(dcol, drow):
    n = sqrt(dcol * dcol + drow * drow)
    if n < 1e-9:
        return (1.0, 0.0)
    return (dcol / n, drow / n)


def limitar(x, minimo, maximo):
    return minimo if x < minimo else maximo if x > maximo else x


def mezcla_diferencial(v, w):
    """(avance, giro) -> (izq, der), escalando para no pasar de |1|."""
    izq = v - w
    der = v + w
    m = max(abs(izq), abs(der))
    if m > 1.0:
        izq /= m
        der /= m
    return izq, der


def comando_hacia_rumbo(theta, theta_deseado, v_max, kp_giro=1.0 / 60.0,
                        w_max=0.6, umbral_girar_quieto=35.0):
    """Control proporcional de rumbo.

    Si el error es grande, gira en el sitio; si no, avanza reduciendo la
    velocidad segun el error. Devuelve (izq, der).
    """
    error = normalizar_180(theta_deseado - theta)
    w = limitar(kp_giro * error, -1.0, 1.0) * w_max
    if abs(error) > umbral_girar_quieto:
        v = 0.0
        # Piso de giro en el sitio: evita quedarse sin fuerza con errores medianos.
        if abs(w) < 0.25:
            w = 0.25 if w >= 0 else -0.25
    else:
        v = v_max * cos(radians(error))
    return mezcla_diferencial(v, w)


def direccion_seguir_linea(rover, cubo, u, ganancia=0.12, correccion_max=0.9):
    """Direccion deseada (dcol, drow) para avanzar a lo largo de `u` corrigiendo
    el desvio lateral del rover respecto de la linea que pasa por el cubo.

    `u` es el vector unitario de empuje (cubo -> depot). Devuelve un vector
    (no necesariamente unitario) que apunta a lo largo de u y hacia la linea.
    """
    rel_col = rover["col"] - cubo["col"]
    rel_row = rover["row"] - cubo["row"]
    perp = (-u[1], u[0])
    lateral = rel_col * perp[0] + rel_row * perp[1]
    corr = limitar(ganancia * lateral, -correccion_max, correccion_max)
    return (u[0] - corr * perp[0], u[1] - corr * perp[1])


def posicion_relativa(rover, cubo, u):
    """(along, lateral): posicion del rover respecto del cubo, en ejes de empuje.
    along < 0 = detras del cubo (del lado opuesto al depot)."""
    rel_col = rover["col"] - cubo["col"]
    rel_row = rover["row"] - cubo["row"]
    perp = (-u[1], u[0])
    return (rel_col * u[0] + rel_row * u[1], rel_col * perp[0] + rel_row * perp[1])


def limitar_a_cancha(punto, grid, margen):
    """Mete un punto {col,row} dentro de la cancha con un margen de seguridad."""
    return {
        "col": limitar(punto["col"], margen, grid["cols"] - margen),
        "row": limitar(punto["row"], margen, grid["rows"] - margen),
    }


def repulsion(rover, otros, radio_influencia=16.0, ganancia=1.6):
    """Vector (dcol, drow) que aleja al rover de los objetos `otros` (con col/row).
    Crece al acercarse y es cero fuera de `radio_influencia`. Se suma a la
    direccion deseada (campo de potencial simple)."""
    rc = rr = 0.0
    for o in otros:
        dc, dr = rover["col"] - o["col"], rover["row"] - o["row"]
        d = sqrt(dc * dc + dr * dr)
        if d >= radio_influencia:
            continue
        if d < 1e-6:
            dc, dr, d = 1.0, 0.0, 1.0
        peso = ganancia * (radio_influencia - d) / radio_influencia
        rc += peso * dc / d
        rr += peso * dr / d
    return rc, rr
