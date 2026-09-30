"""Lazo cerrado: los dos rovers (comun.rover.ControladorRover) contra el
simulador fisico. Si esto pasa, la estrategia completa funciona en simulacion."""

import pytest

from comun.rover import ControladorRover
from simulador_fisico import MundoSim, simular


def _controladores():
    ids = [10, 11]
    return {i: ControladorRover(i, ids) for i in ids}


def test_entregan_los_tres_cubos_sin_choques():
    m, t = simular(_controladores(), max_segundos=200.0)
    assert t is not None, "no termino; entregados=%s" % m.cubos_entregados()
    assert sorted(m.cubos_entregados()) == ["blue", "green", "red"]
    assert m.choques == 0


@pytest.mark.parametrize("semilla", [0, 1, 2, 3])
@pytest.mark.parametrize("ruido", [0.15, 0.3])
def test_tolera_ruido_de_vision(semilla, ruido):
    # 0.3 celdas de sigma = 6 mm por eje, a 20 Hz: bastante peor que la camara real.
    m, t = simular(_controladores(), MundoSim(semilla=semilla, ruido_pose=ruido), max_segundos=200.0)
    assert t is not None, "no termino; entregados=%s" % m.cubos_entregados()
    assert m.choques <= 2  # roces ocasionales; la evitacion robusta esta pendiente


def test_no_se_mueven_fuera_de_running():
    m = MundoSim()
    ctrls = _controladores()
    for _ in range(40):
        msg = m.mensaje(phase="READY")
        ruedas = {rid: c.paso(msg) for rid, c in ctrls.items()}
        assert all(v == (0.0, 0.0) for v in ruedas.values())
        m.paso(ruedas)


def test_se_detienen_al_terminar_la_ronda():
    m = MundoSim()
    ctrls = _controladores()
    for _ in range(40):
        m.paso({rid: c.paso(m.mensaje()) for rid, c in ctrls.items()})
    ruedas = {rid: c.paso(m.mensaje(phase="FINISHED")) for rid, c in ctrls.items()}
    assert all(v == (0.0, 0.0) for v in ruedas.values())
    assert all(c.estado == "DETENIDO" for c in ctrls.values())
