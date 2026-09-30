"""Maquina de estados de un rover. Decide QUE hacer segun el mundo; el COMO
(comandos de rueda) vive en comun/planificador.py.

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
#
# OJO: `col/row` de un rover es el centro de su marcador, y el cubo no puede estar
# mas cerca que radio del chasis (~3 celdas) + mitad del cubo (~1.5) = ~4.5. Por eso
# el umbral de agarre es de varias celdas y no de ~1.
UMBRAL_AGARRE_CELDAS = 6.0
UMBRAL_ENTREGA_CELDAS = 1.0
# Si en TRANSPORTAR el cubo queda mas lejos que esto del rover, se escapo: volver a
# APROXIMAR para recuperarlo.
UMBRAL_CUBO_PERDIDO_CELDAS = 9.0
# Para soltar, el cubo debe estar adentro de la zona con este margen extra por
# lado (celdas): la posicion de vision tiene ruido y en el borde se veria "adentro"
# sin estarlo. El veredicto oficial (sin margen) se usa para confirmar la entrega.
MARGEN_ENTREGA_CELDAS = 1.0


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
          El agarre no es verificable por vision (la camara ve el cubo cerca del
          rover tanto si lo sujeto como si no), asi que esta señal es obligatoria.
        - cubo_entregado: confirmacion adicional del propio rover (opcional). La
          entrega SI es verificable por vision -- una vez soltado, el cubo se
          asienta en una posicion que la camara puede comparar contra la zona
          (protocolo v2: depot_size/cube_side, ver mundo.cubo_en_su_zona) -- asi
          que ENTREGAR tambien sale solo con lo que ve la vision, sin depender de
          que el firmware acierte el sensor.

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
            en_zona = (
                cubo is not None
                and depot is not None
                and msg.get("depot_size") is not None
                and msg.get("cube_side") is not None
                and msg.get("grid") is not None
                and mundo.cubo_en_su_zona(
                    cubo,
                    depot,
                    {
                        "length": msg["depot_size"]["length"] - 2 * MARGEN_ENTREGA_CELDAS,
                        "depth": msg["depot_size"]["depth"] - 2 * MARGEN_ENTREGA_CELDAS,
                    },
                    msg["grid"],
                    msg["cube_side"],
                )[0]
            )
            if en_zona or (
                depot is not None and mundo.distancia(rover, depot) < UMBRAL_ENTREGA_CELDAS
            ):
                self.estado = ESTADO_ENTREGAR
            elif (
                cubo is not None
                and mundo.es_fresco(cubo)
                and mundo.distancia(rover, cubo) > UMBRAL_CUBO_PERDIDO_CELDAS
            ):
                self.estado = ESTADO_APROXIMAR

        elif self.estado == ESTADO_ENTREGAR:
            depot_size = msg.get("depot_size")
            cube_side = msg.get("cube_side")
            grid = msg.get("grid")
            confirmado_por_vision = (
                cubo is not None
                and depot is not None
                and depot_size is not None
                and cube_side is not None
                and grid is not None
                and mundo.cubo_en_su_zona(cubo, depot, depot_size, grid, cube_side)[0]
            )
            if cubo_entregado or confirmado_por_vision:
                self.estado = ESTADO_OCIOSO
            elif (
                cubo is not None
                and mundo.es_fresco(cubo)
                and mundo.distancia(rover, cubo) > UMBRAL_CUBO_PERDIDO_CELDAS
            ):
                # Se solto pero no quedo adentro: ir a empujarlo de nuevo.
                self.estado = ESTADO_APROXIMAR

        # ESTADO_OCIOSO: espera una reasignacion externa (asignar_color) que lo
        # regresa a BUSCAR -- ver comun/protocolo_rovers.py.

        return self.estado
