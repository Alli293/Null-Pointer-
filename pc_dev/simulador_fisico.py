"""Simulador fisico en lazo cerrado: rovers diferenciales que empujan cubos.

No reemplaza al mock_publisher del repo guia (ese solo publica telemetria, no
reacciona a los comandos de los rovers). Este cierra el lazo: toma los comandos
de ruedas de `comun.rover.ControladorRover`, mueve el mundo y genera mensajes de
telemetria v2 para el siguiente paso. Sirve para validar la estrategia completa
sin robot.

Modelo (simple, a proposito): rover = circulo, cubo = circulo, el rover empuja
al cubo al solaparse. Escenario por defecto = config_simulador.json del repo guia.
"""

import math
import random

from comun import contrato, mundo
from comun import navegacion as nav

RADIO_ROVER = 3.0      # celdas (chasis ~120 mm = 6 celdas de diametro)
RADIO_CUBO = 1.6       # celdas (cubo de 3 celdas de lado, ~mitad de la diagonal)
VEL_MAX = 6.0          # celdas/s a comando 1.0 (config_simulador.json)
GIRO_MAX = 90.0        # grados/s a w = 1.0 (config_simulador.json)
DT = 0.05              # 20 Hz, igual que la telemetria real

GRID = {"cols": 43, "rows": 43, "cell_mm": 20.0}
DEPOT_SIZE = {"length": 10.0, "depth": 7.5}
CUBE_SIDE = 3.0
START = {"col": 3.75, "row": 21.5}
DEPOTS = [
    {"color": "green", "col": 21.5, "row": 3.75},
    {"color": "red", "col": 39.25, "row": 21.5},
    {"color": "blue", "col": 21.5, "row": 39.25},
]


def escenario_por_defecto():
    return {
        "rovers": [
            {"id": 10, "col": 4.0, "row": 17.5, "theta": 0.0},
            {"id": 11, "col": 4.0, "row": 25.5, "theta": 0.0},
        ],
        "cubos": [
            {"color": "green", "col": 26.0, "row": 10.0},
            {"color": "blue", "col": 15.0, "row": 29.0},
            {"color": "red", "col": 33.0, "row": 26.0},
        ],
    }


class MundoSim:
    def __init__(self, escenario=None, semilla=0, ruido_pose=0.0):
        esc = escenario or escenario_por_defecto()
        self.rovers = [dict(r) for r in esc["rovers"]]
        self.cubos = [dict(c) for c in esc["cubos"]]
        self.t = 0.0
        self.seq = 0
        self.choques = 0
        self._en_choque = False
        self._rng = random.Random(semilla)
        self._ruido = ruido_pose
        self.ruedas = {r["id"]: (0.0, 0.0) for r in self.rovers}

    # -- fisica ---------------------------------------------------------------
    def _mover_rover(self, r, izq, der):
        v = (izq + der) / 2.0 * VEL_MAX
        w = (der - izq) / 2.0 * GIRO_MAX
        r["theta"] = (r["theta"] + w * DT) % 360.0
        rad = math.radians(r["theta"])
        r["col"] += v * math.cos(rad) * DT
        r["row"] -= v * math.sin(rad) * DT  # row crece hacia abajo
        r["col"] = nav.limitar(r["col"], RADIO_ROVER, GRID["cols"] - RADIO_ROVER)
        r["row"] = nav.limitar(r["row"], RADIO_ROVER, GRID["rows"] - RADIO_ROVER)

    def _empujar_cubos(self):
        minimo = RADIO_ROVER + RADIO_CUBO
        for c in self.cubos:
            for r in self.rovers:
                dcol, drow = c["col"] - r["col"], c["row"] - r["row"]
                d = math.hypot(dcol, drow)
                if d < minimo:
                    if d < 1e-6:
                        dcol, drow, d = 1.0, 0.0, 1.0
                    c["col"] = r["col"] + dcol / d * minimo
                    c["row"] = r["row"] + drow / d * minimo
            c["col"] = nav.limitar(c["col"], RADIO_CUBO, GRID["cols"] - RADIO_CUBO)
            c["row"] = nav.limitar(c["row"], RADIO_CUBO, GRID["rows"] - RADIO_CUBO)

    def _contar_choques(self):
        if len(self.rovers) < 2:
            return
        a, b = self.rovers[0], self.rovers[1]
        chocan = mundo.distancia(a, b) < 2 * RADIO_ROVER
        if chocan and not self._en_choque:
            self.choques += 1
        self._en_choque = chocan

    def paso(self, ruedas_por_id):
        """Avanza DT segundos aplicando {rover_id: (izq, der)}."""
        for r in self.rovers:
            izq, der = ruedas_por_id.get(r["id"], (0.0, 0.0))
            self.ruedas[r["id"]] = (izq, der)
            self._mover_rover(r, izq, der)
        self._empujar_cubos()
        self._contar_choques()
        self.t += DT
        self.seq += 1

    # -- sensores y telemetria ---------------------------------------------------
    def tiene_cubo(self, rover_id):
        """Sensor de agarre simulado: cubo pegado al frente del rover."""
        r = next(x for x in self.rovers if x["id"] == rover_id)
        for c in self.cubos:
            d = mundo.distancia(r, c)
            if d <= RADIO_ROVER + RADIO_CUBO + 0.6:
                rumbo = nav.rumbo_hacia(r, c)
                if abs(nav.normalizar_180(rumbo - r["theta"])) < 40.0:
                    return True
        return False

    def mensaje(self, phase="RUNNING", total_ms=600_000):
        def con_ruido(x):
            return x + self._rng.gauss(0.0, self._ruido) if self._ruido else x

        elapsed = int(self.t * 1000)
        return {
            "v": 2,
            "seq": self.seq,
            "ts_ms": 1_700_000_000_000 + elapsed,
            "phase": phase,
            "clock": {
                "elapsed_ms": elapsed,
                "remaining_ms": max(0, total_ms - elapsed),
                "total_ms": total_ms,
            },
            "grid": GRID,
            "rovers": [
                {"id": r["id"], "col": con_ruido(r["col"]), "row": con_ruido(r["row"]),
                 "theta": r["theta"], "age_ms": 0}
                for r in self.rovers
            ],
            "cubes": [
                {"color": c["color"], "col": con_ruido(c["col"]), "row": con_ruido(c["row"]),
                 "age_ms": 0}
                for c in self.cubos
            ],
            "obstacles": [],
            "start": START,
            "depots": DEPOTS,
            "depot_size": DEPOT_SIZE,
            "cube_side": CUBE_SIDE,
        }

    def cubos_entregados(self):
        """Colores cuyo cubo esta completamente dentro de su zona (criterio oficial)."""
        entregados = []
        for c in self.cubos:
            dep = next(d for d in DEPOTS if d["color"] == c["color"])
            if mundo.cubo_en_su_zona(c, dep, DEPOT_SIZE, GRID, CUBE_SIDE)[0]:
                entregados.append(c["color"])
        return entregados


def simular(controladores, mundo_sim=None, max_segundos=300.0):
    """Corre el lazo cerrado. `controladores` = {rover_id: ControladorRover}.

    Devuelve (mundo_sim, segundos_hasta_terminar o None si no termino).
    """
    m = mundo_sim or MundoSim()
    total = len(m.cubos)
    while m.t < max_segundos:
        msg = m.mensaje()
        ruedas = {
            rid: ctrl.paso(msg, tiene_cubo=m.tiene_cubo(rid))
            for rid, ctrl in controladores.items()
        }
        m.paso(ruedas)
        if len(m.cubos_entregados()) == total:
            return m, m.t
    return m, None
