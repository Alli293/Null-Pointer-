import json
from comun.coordinacion import Coordinador, mac48, repartir
from simulador_fisico import MundoSim


def pareja():
    return (Coordinador(bytes([0, 0, 0, 0, 0, 1]), bytes([0, 0, 0, 0, 0, 2]),
                        [10, 11], 10, "a"),
            Coordinador(bytes([0, 0, 0, 0, 0, 2]), bytes([0, 0, 0, 0, 0, 1]),
                        [10, 11], 11, "b"))


def intercambiar(a, b, t, done=True):
    b.recibir(a.mensaje(done), t)
    a.recibir(b.mensaje(done), t)


def test_mac_48_bits():
    assert mac48(bytes([255] * 6)) == 2 ** 48 - 1
    assert mac48(bytes([1, 0, 0, 0, 0, 0])) == 1 << 40
    a, b = pareja()
    assert b.lider and not a.lider


def test_asignacion_y_confirmacion():
    a, b = pareja()
    msg = MundoSim().mensaje()
    intercambiar(a, b, 0)
    intercambiar(a, b, 100)
    b.actualizar(msg, 100, True)
    assert len(set(b.plan)) == 2 and None not in b.plan
    assert not b.autorizado(100)  # necesita ACK del nuevo plan
    intercambiar(a, b, 200)
    intercambiar(a, b, 300)
    assert a.plan == b.plan and b.autorizado(300)
    assert not a.autorizado(1100) and not b.autorizado(1100)
    assert len(json.dumps(b.mensaje(False)).encode()) <= 250


def test_cercania_tercero_y_entregados():
    msg = MundoSim().mensaje()
    for r, col in zip(msg["rovers"], (10, 30)):
        r.update(col=col, row=20, age_ms=0)
    for c, col in zip(msg["cubes"], (11, 29, 20)):
        c.update(col=col, row=20, age_ms=0)
    colores = [c["color"] for c in msg["cubes"]]
    assert repartir(msg, [10, 11]) == colores[:2]
    for c in msg["cubes"][:2]:
        d = next(d for d in msg["depots"] if d["color"] == c["color"])
        c.update(col=d["col"], row=d["row"])
    msg["rovers"][1]["col"] = 21
    assert repartir(msg, [10, 11]) == [None, colores[2]]


def test_no_reasigna_durante_trabajo_y_rechaza_repetidos():
    a, b = pareja()
    intercambiar(a, b, 0)
    intercambiar(a, b, 10)
    msg = MundoSim().mensaje()
    b.actualizar(msg, 10, True)
    original = list(b.plan)
    intercambiar(a, b, 20, False)
    b.actualizar(msg, 20, False)
    assert b.plan == original
    p = b.mensaje(False)
    a.recibir(p, 30)
    a.recibir(p, 700)
    assert not a.autorizado(800)


def test_no_asigna_con_rover_oculto():
    msg = MundoSim().mensaje()
    msg["rovers"][0]["age_ms"] = 5000
    assert repartir(msg, [10, 11]) == [None, None]


def test_ciclo_completo_con_radio_y_perdidas():
    from comun.rover import ControladorRover
    a, b = pareja()
    coords = {10: a, 11: b}
    ctrls = {rid: ControladorRover(rid, [10, 11], coordinado=True) for rid in coords}
    sim = MundoSim()
    for tick in range(4000):
        ahora = tick * 50
        msg = sim.mensaje()
        done = {rid: c.fsm.color_asignado is None or c.estado == "OCIOSO"
                for rid, c in ctrls.items()}
        # Perder uno de cada cinco intercambios, incluido el primero.
        if tick % 5:
            b.recibir(a.mensaje(done[10]), ahora)
            a.recibir(b.mensaje(done[11]), ahora)
        ruedas = {}
        for rid, coord in coords.items():
            coord.actualizar(msg, ahora, done[rid])
            ctrls[rid].asignar(coord.plan[coord.indice])
            ruedas[rid] = (ctrls[rid].paso(msg, sim.tiene_cubo(rid))
                           if coord.autorizado(ahora) else (0, 0))
        sim.paso(ruedas)
        if len(sim.cubos_entregados()) == 3:
            break
    assert len(sim.cubos_entregados()) == 3, sim.cubos_entregados()
    assert sim.choques == 0


def test_reinicio_del_seguidor_retira_plan_y_exige_handshake():
    a, b = pareja()
    intercambiar(a, b, 0)
    intercambiar(a, b, 10)
    b.actualizar(MundoSim().mensaje(), 10, True)
    a2, _ = pareja()
    a2.sesion = "nuevo"
    b.recibir(a2.mensaje(True), 20)
    assert b.plan == [None, None]
    assert not b.autorizado(20)


def test_controlador_frena_con_cubo_o_pose_viejos():
    from comun.rover import ControladorRover
    c = ControladorRover(10, [10, 11], coordinado=True)
    msg = MundoSim().mensaje()
    c.asignar(msg["cubes"][0]["color"])
    msg["cubes"][0]["age_ms"] = 2000
    assert c.paso(msg) == (0, 0)
    msg["cubes"][0]["age_ms"] = 0
    msg["rovers"][0]["age_ms"] = 2000
    assert c.paso(msg) == (0, 0)
