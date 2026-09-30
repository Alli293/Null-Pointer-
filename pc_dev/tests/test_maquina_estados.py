from comun.maquina_estados import (
    RoverFSM,
    ESTADO_BUSCAR,
    ESTADO_APROXIMAR,
    ESTADO_SUJETAR,
    ESTADO_TRANSPORTAR,
    ESTADO_ENTREGAR,
    ESTADO_OCIOSO,
    ESTADO_DETENIDO,
)

import datos_ejemplo as d


def test_arranca_en_buscar():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    assert fsm.estado == ESTADO_BUSCAR


def test_buscar_a_aproximar_con_cubo_fresco():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    estado = fsm.transicion(d.MSG_NORMAL)
    assert estado == ESTADO_APROXIMAR


def test_aproximar_vuelve_a_buscar_si_cubo_se_ocluye():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.transicion(d.MSG_NORMAL)  # -> APROXIMAR
    estado = fsm.transicion(d.MSG_CUBO_OCLUIDO)
    assert estado == ESTADO_BUSCAR


def test_aproximar_a_sujetar_por_distancia():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.transicion(d.MSG_NORMAL)  # -> APROXIMAR
    estado = fsm.transicion(d.MSG_CUBO_CERCA)
    assert estado == ESTADO_SUJETAR


def test_sujetar_a_transportar_cuando_sensor_confirma():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.transicion(d.MSG_NORMAL)
    fsm.transicion(d.MSG_CUBO_CERCA)  # -> SUJETAR
    estado = fsm.transicion(d.MSG_CUBO_CERCA, tiene_cubo=True)
    assert estado == ESTADO_TRANSPORTAR


def test_transportar_a_entregar_por_distancia_a_depot():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.estado = ESTADO_TRANSPORTAR
    estado = fsm.transicion(d.MSG_ROVER_EN_DEPOT)
    assert estado == ESTADO_ENTREGAR


def test_entregar_a_ocioso_cuando_sensor_confirma():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.estado = ESTADO_ENTREGAR
    # El cubo en MSG_ROVER_EN_DEPOT sigue lejos del depot (vision no lo confirmaria);
    # solo pasa a OCIOSO porque el sensor del propio rover lo confirma.
    estado = fsm.transicion(d.MSG_ROVER_EN_DEPOT, cubo_entregado=True)
    assert estado == ESTADO_OCIOSO


def test_entregar_a_ocioso_confirmado_solo_por_vision():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.estado = ESTADO_ENTREGAR
    # Sin cubo_entregado (sensor no dice nada) -- pero la vision ve el cubo
    # asentado dentro de su zona, y eso alcanza (protocolo v2).
    estado = fsm.transicion(d.MSG_CUBO_ENTREGADO)
    assert estado == ESTADO_OCIOSO


def test_entregar_no_pasa_a_ocioso_si_cubo_sigue_lejos():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.estado = ESTADO_ENTREGAR
    estado = fsm.transicion(d.MSG_ROVER_EN_DEPOT)  # sin sensor, cubo lejos del depot
    assert estado == ESTADO_ENTREGAR


def test_finished_detiene_desde_cualquier_estado():
    for estado_inicial in (
        ESTADO_BUSCAR, ESTADO_APROXIMAR, ESTADO_SUJETAR,
        ESTADO_TRANSPORTAR, ESTADO_ENTREGAR, ESTADO_OCIOSO,
    ):
        fsm = RoverFSM(mi_id=10, color_asignado="green")
        fsm.estado = estado_inicial
        estado = fsm.transicion(d.MSG_FINISHED)
        assert estado == ESTADO_DETENIDO


def test_detenido_es_terminal_hasta_reasignar():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.estado = ESTADO_DETENIDO
    estado = fsm.transicion(d.MSG_NORMAL)  # aunque llegue telemetria normal
    assert estado == ESTADO_DETENIDO


def test_asignar_color_reactiva_desde_ocioso():
    fsm = RoverFSM(mi_id=10, color_asignado="green")
    fsm.estado = ESTADO_OCIOSO
    fsm.asignar_color("blue")
    assert fsm.estado == ESTADO_BUSCAR
    assert fsm.color_asignado == "blue"
