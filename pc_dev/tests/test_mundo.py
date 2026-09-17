from comun import contrato, mundo

import datos_ejemplo as d


def test_mi_rover_encuentra_por_id():
    rover = mundo.mi_rover(d.MSG_NORMAL, 10)
    assert rover is not None
    assert rover["id"] == 10


def test_mi_rover_none_si_no_esta():
    assert mundo.mi_rover(d.MSG_NORMAL, 99) is None


def test_cubo_por_color():
    cubo = mundo.cubo_por_color(d.MSG_NORMAL, "green")
    assert cubo is not None
    assert cubo["color"] == "green"
    assert mundo.cubo_por_color(d.MSG_NORMAL, "red") is None  # no hay cubo rojo en este frame


def test_depot_por_color():
    depot = mundo.depot_por_color(d.MSG_NORMAL, "blue")
    assert depot == {"color": "blue", "col": 21.5, "row": 39.25}


def test_clasificar_frescura_umbrales():
    assert mundo.clasificar_frescura(0) == contrato.FRESCO
    assert mundo.clasificar_frescura(199) == contrato.FRESCO
    assert mundo.clasificar_frescura(200) == contrato.DUDOSO
    assert mundo.clasificar_frescura(1499) == contrato.DUDOSO
    assert mundo.clasificar_frescura(1500) == contrato.NO_CONFIABLE


def test_es_fresco_cubo_ocluido():
    cubo = mundo.cubo_por_color(d.MSG_CUBO_OCLUIDO, "green")
    assert not mundo.es_fresco(cubo)


def test_es_fresco_depot_siempre_true():
    depot = mundo.depot_por_color(d.MSG_NORMAL, "green")
    assert mundo.es_fresco(depot)  # los depots no traen age_ms


def test_distancia():
    rover = mundo.mi_rover(d.MSG_CUBO_CERCA, 10)
    cubo = mundo.cubo_por_color(d.MSG_CUBO_CERCA, "green")
    assert mundo.distancia(rover, cubo) < 1.0


def test_validar_version():
    assert contrato.validar_version(d.MSG_NORMAL)
    assert not contrato.validar_version(d.MSG_VERSION_INVALIDA)


def test_estimador_latencia_offset_constante_no_alarma():
    est = mundo.EstimadorLatencia()
    msg1 = dict(d.MSG_NORMAL, ts_ms=1000)
    msg2 = dict(d.MSG_NORMAL, ts_ms=1050)
    assert est.actualizar(msg1, ahora_ms=5000) == 0  # primera muestra: fija el offset base
    # mismo offset (4000) en la segunda muestra -> sin variacion
    assert est.actualizar(msg2, ahora_ms=5050) == 0


def test_estimador_latencia_detecta_crecimiento():
    est = mundo.EstimadorLatencia()
    msg1 = dict(d.MSG_NORMAL, ts_ms=1000)
    msg2 = dict(d.MSG_NORMAL, ts_ms=1050)
    est.actualizar(msg1, ahora_ms=5000)  # offset base = 4000
    # ahora el offset crecio a 4600 (600 mas) -> los mensajes se estan atrasando
    variacion = est.actualizar(msg2, ahora_ms=5650)
    assert variacion == 600


def test_mensaje_utilizable_rechaza_version_invalida():
    est = mundo.EstimadorLatencia()
    assert not mundo.mensaje_utilizable(d.MSG_VERSION_INVALIDA, 0, est)


def test_mensaje_utilizable_rechaza_idle():
    est = mundo.EstimadorLatencia()
    assert not mundo.mensaje_utilizable(d.MSG_IDLE, 0, est)


def test_mensaje_utilizable_acepta_running():
    est = mundo.EstimadorLatencia()
    assert mundo.mensaje_utilizable(d.MSG_NORMAL, d.MSG_NORMAL["ts_ms"], est)


def test_cubo_en_su_zona_exactamente_en_el_centro():
    # Mismo caso que el ejemplo de la seccion 2 del contrato: (21.480, 3.762)
    # contra una zona centrada en (21.5, 3.75) da (True, 0.0).
    cubo = {"color": "green", "col": 21.480, "row": 3.762, "age_ms": 0}
    depot = d.DEPOTS[0]  # green, (21.5, 3.75)
    adentro, falta = mundo.cubo_en_su_zona(cubo, depot, d.DEPOT_SIZE, d.GRID, d.CUBE_SIDE)
    assert adentro
    assert falta < 0.01


def test_cubo_en_su_zona_lejos_del_depot():
    cubo = mundo.cubo_por_color(d.MSG_ROVER_EN_DEPOT, "green")  # (26.0, 10.0)
    depot = d.DEPOTS[0]
    adentro, falta = mundo.cubo_en_su_zona(cubo, depot, d.DEPOT_SIZE, d.GRID, d.CUBE_SIDE)
    assert not adentro
    assert falta > 0


def test_cubo_en_su_zona_msg_cubo_entregado():
    cubo = mundo.cubo_por_color(d.MSG_CUBO_ENTREGADO, "green")
    depot = mundo.depot_por_color(d.MSG_CUBO_ENTREGADO, "green")
    adentro, _ = mundo.cubo_en_su_zona(
        cubo, depot, d.MSG_CUBO_ENTREGADO["depot_size"], d.MSG_CUBO_ENTREGADO["grid"], d.MSG_CUBO_ENTREGADO["cube_side"]
    )
    assert adentro


def test_tiempo_restante_ms():
    assert mundo.tiempo_restante_ms(d.MSG_NORMAL) == d.MSG_NORMAL["clock"]["remaining_ms"]
    assert mundo.tiempo_restante_ms({"phase": "IDLE"}) is None  # sin clock -> None
