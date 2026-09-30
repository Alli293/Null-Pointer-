import sys
sys.path.insert(0, "..")
from comun.rover import ControladorRover
from simulador_fisico import MundoSim, DT
ruido = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 120
m = MundoSim(semilla=1, ruido_pose=ruido); ids=[10,11]
C = {i: ControladorRover(i, ids) for i in ids}
prev = {}; ch = 0
for k in range(int(dur/DT)):
    msg = m.mensaje()
    ru = {i: c.paso(msg, tiene_cubo=m.tiene_cubo(i)) for i, c in C.items()}
    m.paso(ru)
    if m.choques != ch:
        ch = m.choques
        print("!! CHOQUE t=%.1f" % m.t, [(r["id"], round(r["col"],1), round(r["row"],1), round(r["theta"])) for r in m.rovers], {i: C[i].estado for i in C})
    for i, c in C.items():
        key = (c.estado, c.fsm.color_asignado)
        if prev.get(i) != key:
            r = next(x for x in m.rovers if x["id"] == i)
            print("t=%6.1f rover%d %s %s pos=(%.1f,%.1f) th=%.0f" % (m.t, i, c.estado, c.fsm.color_asignado, r["col"], r["row"], r["theta"]))
            prev[i] = key
print("choques", m.choques, "entregados", m.cubos_entregados(), "t=", round(m.t))
