"""Maquina de estados de un rover. Decide QUE hacer segun el mundo; el COMO
(comandos de motor concretos) vive en firmware/movimiento.py.

Ver docs/arquitectura.md para el diagrama de estados y el razonamiento detras de
cada transicion.
"""

from comun import contrato, mundo

ESTADO_BUSCAR = "BUSCAR"
ESTADO_APROXIMAR = "APROXIMAR"
ESTADO_SUJETAR = "SUJETAR"
ESTADO_TRANSPORTAR = "TRANSPORTAR"
ESTADO_ENTREGAR = "ENTREGAR"
ESTADO_OCIOSO = "OCIOSO"
ESTADO_DETENIDO = "DETENIDO"

# Umbrales de distancia (en celdas) para considerar que el rover ya esta lo
# bastante cerca del cubo/depot como para intentar agarrar/soltar. Son un punto de
# partida -- afinar con pruebas fisicas una vez calibrados los sensores/paletas.
UMBRAL_AGARRE_CELDAS = 1.0
UMBRAL_ENTREGA_CELDAS = 1.0


class RoverFSM:
    """Maquina de estados de un rover para un color de cubo asignado a la vez.

    `color_asignado` puede reasignarse en caliente (ver comun/protocolo_rovers.py)
    cuando el rover queda OCIOSO y el equipo decide que tome otro color.
    """

    def __init__(self, mi_id, color_asignado):
        self.mi_id = mi_id
        self.color_asignado = color_asignado
        self.estado = ESTADO_BUSCAR

    def asignar_color(self, color):
        self.color_asignado = color
        if self.estado == ESTADO_OCIOSO:
            self.estado = ESTADO_BUSCAR

    def transicion(self, msg, tiene_cubo=False, cubo_entregado=False):
        """Actualiza self.estado a partir de un mensaje de telemetria ya validado
        (ver mundo.mensaje_utilizable) y de dos señales que solo el firmware conoce
        via sus propios sensores (no vienen de la vision):

        - tiene_cubo: el rover confirmo que sujeto el cubo (sensor de color/IR/switch).
        - cubo_entregado: el rover confirmo que solto el cubo dentro del depot.

        Devuelve el nuevo estado.
        """
        # FINISHED manda siempre, sin importar el estado actual (regla de fases).
        if msg.get("phase") == contrato.FASE_FINISHED:
            self.estado = ESTADO_DETENIDO
            return self.estado

        if self.estado == ESTADO_DETENIDO:
            # Una vez detenido por FINISHED, solo se reactiva con una nueva ronda
            # (fase READY) reasignando color explicitamente desde afuera.
            return self.estado

        rover = mundo.mi_rover(msg, self.mi_id)
        if rover is None or self.color_asignado is None:
            return self.estado

        cubo = mundo.cubo_por_color(msg, self.color_asignado)
        depot = mundo.depot_por_color(msg, self.color_asignado)

        if self.estado == ESTADO_BUSCAR:
            if cubo is not None and mundo.es_fresco(cubo):
                self.estado = ESTADO_APROXIMAR

        elif self.estado == ESTADO_APROXIMAR:
            if cubo is None or not mundo.es_fresco(cubo):
                self.estado = ESTADO_BUSCAR
            elif mundo.distancia(rover, cubo) < UMBRAL_AGARRE_CELDAS:
                self.estado = ESTADO_SUJETAR

        elif self.estado == ESTADO_SUJETAR:
            if tiene_cubo:
                self.estado = ESTADO_TRANSPORTAR
            elif cubo is None or not mundo.es_fresco(cubo):
                # Se nos "perdio" el cubo (lo movio el otro rover, oclusion, etc.)
                self.estado = ESTADO_BUSCAR

        elif self.estado == ESTADO_TRANSPORTAR:
            if depot is not None and mundo.distancia(rover, depot) < UMBRAL_ENTREGA_CELDAS:
                self.estado = ESTADO_ENTREGAR

        elif self.estado == ESTADO_ENTREGAR:
            if cubo_entregado:
                self.estado = ESTADO_OCIOSO

        # ESTADO_OCIOSO: espera una reasignacion externa (asignar_color) que lo
        # regresa a BUSCAR -- ver comun/protocolo_rovers.py.

        return self.estado
