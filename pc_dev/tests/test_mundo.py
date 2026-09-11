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
    assert depot == {"color": "blue", "col": 40.5, "row": 40.5}


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
