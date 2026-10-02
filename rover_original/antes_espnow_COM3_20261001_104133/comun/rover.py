"""Controlador de un rover: junta FSM + planificador + asignacion de colores.

`paso(msg, tiene_cubo)` recibe un mensaje de telemetria ya validado y devuelve
el comando de ruedas (izq, der). Lo usan igual el firmware y el simulador de
pc_dev/, asi lo que se prueba en la PC es lo que corre en el robot.

El firmware usa coordinado=True y asignar(color) con planes ESP-NOW. El modo
estatico por defecto conserva las simulaciones anteriores. La cesion de paso
sigue siendo basica, no un planificador de rutas con obstaculos.
"""

from comun import contrato, mundo
from comun import navegacion as nav
from comun.maquina_estados import ESTADO_OCIOSO, RoverFSM
from comun.planificador import Planificador, VEL_RETROCESO
from comun.protocolo_rovers import asignacion_estatica

# Un cubo a menos de esto del rover, estando OCIOSO, significa que acabamos de
# soltarlo: hay que retroceder antes de ir por el siguiente.
DIST_LIBERADO = 8.0
# Cesion de paso (el rover de id mayor cede; el de id menor tiene prioridad):
# - el que cede se queda quieto si el otro esta cerca y de frente, y se aparta
#   (reversa) si ademas esta demasiado cerca;
# - el de prioridad solo frena de emergencia si el otro queda casi encima.
# MAX_TICKS_CESION evita que una espera quede bloqueada para siempre.
DIST_CESION = 11.0
DIST_RETROCESO_CESION = 9.0
DIST_FRENO_EMERGENCIA = 8.0
ANGULO_FRENTE = 90.0
MAX_TICKS_CESION = 40
VENTANA_QUIETO_TICKS = 20   # ~1 s a 20 Hz
UMBRAL_QUIETO_CELDAS = 0.5


class ControladorRover:
    def __init__(self, mi_id, ids_rovers, planificador=None, coordinado=False):
        self.mi_id = mi_id
        reparto = asignacion_estatica(ids_rovers)
        self._cola = list(reparto[mi_id])
        self.coordinado = coordinado
        if coordinado:
            self._cola = []
        self._indice = 0
        color = self._cola[0] if self._cola else None
        self.fsm = RoverFSM(mi_id, color)
        self.planificador = planificador or Planificador()
        self._ticks_cediendo = 0
        self._ref = {}  # id -> [col, row, ticks]: para saber si el otro esta quieto

    @property
    def estado(self):
        return self.fsm.estado

    def asignar(self, color):
        if color != self.fsm.color_asignado:
            self.fsm = RoverFSM(self.mi_id, color)
            self._ticks_cediendo = 0

    def _siguiente_color(self):
        self._indice += 1
        if self._indice < len(self._cola):
            return self._cola[self._indice]
        return None

    def _esta_quieto(self, otro):
        """True si el otro rover casi no se movio en la ultima ventana (~1 s)."""
        ref = self._ref.get(otro["id"])
        if ref is None:
            self._ref[otro["id"]] = [otro["col"], otro["row"], 0, False]
            return False
        ref[2] += 1
        if ref[2] >= VENTANA_QUIETO_TICKS:
            ref[3] = mundo.distancia(otro, {"col": ref[0], "row": ref[1]}) < UMBRAL_QUIETO_CELDAS
            ref[0], ref[1], ref[2] = otro["col"], otro["row"], 0
        return ref[3]

    def _cesion(self, msg, rover):
        """None si no hay que ceder; si hay, (izq, der) para quedarse quieto o
        apartarse. Un rover quieto no se cede: se lo rodea (repulsion)."""
        for otro in msg.get("rovers", []):
            if otro["id"] == self.mi_id or self._esta_quieto(otro):
                continue
            d = mundo.distancia(rover, otro)
            rumbo = nav.rumbo_hacia(rover, otro)
            de_frente = abs(nav.normalizar_180(rumbo - rover["theta"])) < ANGULO_FRENTE
            if self.mi_id > otro["id"]:
                if de_frente and d < DIST_RETROCESO_CESION:
                    return (VEL_RETROCESO, VEL_RETROCESO)
                if de_frente and d < DIST_CESION:
                    return (0.0, 0.0)
            elif de_frente and d < DIST_FRENO_EMERGENCIA:
                return (0.0, 0.0)
        return None

    def paso(self, msg, tiene_cubo=False):
        if msg.get("phase") != contrato.FASE_RUNNING:
            # READY/IDLE: no mover. FINISHED: ademas detener la maquina de estados.
            self.fsm.transicion(msg, tiene_cubo=tiene_cubo)
            return (0.0, 0.0)

        rover = mundo.mi_rover(msg, self.mi_id)
        if rover is None or not mundo.es_fresco(rover):
            return (0.0, 0.0)

        if self.coordinado:
            cubo = mundo.cubo_por_color(msg, self.fsm.color_asignado)
            if cubo is None or not mundo.es_fresco(cubo):
                return (0.0, 0.0)

        estado = self.fsm.transicion(msg, tiene_cubo=tiene_cubo)

        if estado == ESTADO_OCIOSO:
            if self.coordinado:
                return (0.0, 0.0)
            if any(mundo.distancia(rover, c) < DIST_LIBERADO for c in msg.get("cubes", [])):
                return (VEL_RETROCESO, VEL_RETROCESO)
            siguiente = self._siguiente_color()
            if siguiente is not None:
                self.fsm.asignar_color(siguiente)
            return (0.0, 0.0)

        cesion = self._cesion(msg, rover)
        if cesion is not None and self._ticks_cediendo < MAX_TICKS_CESION:
            self._ticks_cediendo += 1
            return cesion
        self._ticks_cediendo = 0

        otros = [r for r in msg.get("rovers", []) if r["id"] != self.mi_id]
        return self.planificador.comando(estado, msg, rover, self.fsm.color_asignado, otros)
