"""Planificador de movimiento: dado el estado del FSM y el mundo, devuelve el
comando de ruedas (izq, der). Sin hardware: se prueba con el simulador de pc_dev/.

Estrategia: el cubo se EMPUJA con el frente del rover (entre las paletas) en la
direccion cubo -> depot. Para eso el rover primero se ubica DETRAS del cubo (del
lado opuesto al depot) y luego avanza siguiendo esa linea, corrigiendo el desvio
lateral.

Todos los numeros de abajo (celdas, velocidades) son puntos de partida: calibrar
en banco con el robot real.
"""

from comun import mundo
from comun import navegacion as nav
from comun.maquina_estados import (
    ESTADO_APROXIMAR,
    ESTADO_ENTREGAR,
    ESTADO_SUJETAR,
    ESTADO_TRANSPORTAR,
)

DIST_PREAGARRE = 10.0     # celdas detras del cubo donde se alinea el rover
DIST_LATERAL_RODEO = 10.0  # celdas al costado de la linea para rodear el cubo
MARGEN_CANCHA = 4.0       # el rover (radio ~3) no debe acercarse mas al borde
CONO_ALINEADO = 1.2       # desvio lateral tolerado para ir directo al cubo
VEL_CRUCERO = 0.7
VEL_EMPUJE = 0.5
VEL_RETROCESO = -0.45


def _vec(a, b):
    return b["col"] - a["col"], b["row"] - a["row"]


class Planificador:
    def __init__(self, vel_crucero=VEL_CRUCERO, vel_empuje=VEL_EMPUJE, ganancia_repulsion=0.0):
        self.vel_crucero = vel_crucero
        self.vel_empuje = vel_empuje
        # 0 = apagada. Con el simulador, una repulsion activa empeora el empuje de
        # cubos; la evitacion robusta de colisiones queda para la etapa de
        # coordinacion (ver docs/arquitectura.md).
        self.ganancia_repulsion = ganancia_repulsion

    def comando(self, estado, msg, rover, color, otros=()):
        """(izq, der) para el estado actual. `color` es el cubo asignado y `otros`
        son los demas rovers (de los que se aleja con un campo de repulsion)."""
        if estado == ESTADO_ENTREGAR:
            return (VEL_RETROCESO, VEL_RETROCESO)
        if estado not in (ESTADO_APROXIMAR, ESTADO_SUJETAR, ESTADO_TRANSPORTAR):
            return (0.0, 0.0)

        cubo = mundo.cubo_por_color(msg, color)
        depot = mundo.depot_por_color(msg, color)
        if cubo is None or depot is None:
            return (0.0, 0.0)

        u = nav.unitario(*_vec(cubo, depot))
        along, lateral = nav.posicion_relativa(rover, cubo, u)

        if estado == ESTADO_APROXIMAR:
            direccion, vel, umbral = self._aproximar(rover, cubo, u, along, lateral, msg["grid"])
        else:
            # SUJETAR / TRANSPORTAR: empujar a lo largo de la linea cubo -> depot.
            direccion, vel, umbral = self._empujar(rover, cubo, u, self.vel_empuje)

        # Alejarse de los otros rovers sin perder el objetivo: se suma la repulsion
        # a la direccion deseada (normalizada).
        d = nav.unitario(direccion[0], direccion[1])
        rc, rr = nav.repulsion(rover, otros, ganancia=self.ganancia_repulsion)
        objetivo = nav.rumbo_de_vector(d[0] + rc, d[1] + rr)
        return nav.comando_hacia_rumbo(
            rover["theta"], objetivo, vel, umbral_girar_quieto=umbral
        )

    def _empujar(self, rover, cubo, u, velocidad):
        dv = nav.direccion_seguir_linea(rover, cubo, u)
        # Al empujar, el rumbo tiene que estar bien alineado: girar quieto desde 20 grados.
        return dv, velocidad, 20.0

    def _aproximar(self, rover, cubo, u, along, lateral, grid):
        detras_alineado = along < 0 and abs(lateral) < CONO_ALINEADO + 0.10 * (-along)
        if detras_alineado:
            dist = mundo.distancia(rover, cubo)
            vel = self.vel_crucero if dist > DIST_PREAGARRE + 4 else self.vel_empuje
            return self._empujar(rover, cubo, u, vel)

        perp = (-u[1], u[0])
        if along > -3.0 and abs(lateral) < DIST_LATERAL_RODEO * 0.8:
            # Estoy del lado del depot o pegado al cubo (y aun no al costado): rodear.
            signo = 1.0 if lateral >= 0 else -1.0
            objetivo_pt = {
                "col": cubo["col"] + perp[0] * signo * DIST_LATERAL_RODEO - u[0] * 2.0,
                "row": cubo["row"] + perp[1] * signo * DIST_LATERAL_RODEO - u[1] * 2.0,
            }
        else:
            objetivo_pt = {
                "col": cubo["col"] - u[0] * DIST_PREAGARRE,
                "row": cubo["row"] - u[1] * DIST_PREAGARRE,
            }
        objetivo_pt = nav.limitar_a_cancha(objetivo_pt, grid, MARGEN_CANCHA)
        return _vec(rover, objetivo_pt), self.vel_crucero, 35.0
