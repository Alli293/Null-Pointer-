from comun import navegacion as nav


def test_normalizar_180():
    assert nav.normalizar_180(190) == -170
    assert nav.normalizar_180(-190) == 170
    assert nav.normalizar_180(0) == 0


def test_rumbo_respeta_row_hacia_abajo():
    o = {"col": 10, "row": 10}
    assert round(nav.rumbo_hacia(o, {"col": 20, "row": 10})) == 0      # derecha
    assert round(nav.rumbo_hacia(o, {"col": 10, "row": 0})) == 90      # arriba en pantalla
    assert round(nav.rumbo_hacia(o, {"col": 0, "row": 10})) == 180     # izquierda
    assert round(nav.rumbo_hacia(o, {"col": 10, "row": 20})) == 270    # abajo


def test_mezcla_diferencial_escala_a_uno():
    izq, der = nav.mezcla_diferencial(1.0, 0.5)
    assert max(abs(izq), abs(der)) == 1.0


def test_giro_antihorario_acelera_rueda_derecha():
    # objetivo a 90 grados antihorario de la orientacion actual -> girar a la izquierda
    izq, der = nav.comando_hacia_rumbo(0, 90, 0.7)
    assert der > izq


def test_error_grande_gira_en_el_sitio():
    izq, der = nav.comando_hacia_rumbo(0, 120, 0.7)
    assert izq < 0 < der and abs(izq + der) < 1e-9


def test_alineado_avanza_recto():
    izq, der = nav.comando_hacia_rumbo(45, 45, 0.7)
    assert abs(izq - der) < 1e-9 and izq > 0


def test_posicion_relativa_detras_del_cubo():
    cubo = {"col": 20, "row": 20}
    u = (1.0, 0.0)  # empujar hacia col creciente
    along, lateral = nav.posicion_relativa({"col": 10, "row": 20}, cubo, u)
    assert along == -10 and lateral == 0


def test_limitar_a_cancha():
    p = nav.limitar_a_cancha({"col": -5, "row": 100}, {"cols": 43, "rows": 43}, 4)
    assert p == {"col": 4, "row": 39}


def test_repulsion_cero_fuera_de_radio_y_aleja_dentro():
    r = {"col": 10, "row": 10}
    assert nav.repulsion(r, [{"col": 40, "row": 10}]) == (0.0, 0.0)
    rc, rr = nav.repulsion(r, [{"col": 14, "row": 10}])
    assert rc < 0 and rr == 0
