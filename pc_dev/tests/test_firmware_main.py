"""Ejecuta firmware/main.py en la PC con modulos de hardware falsos.

No prueba el hardware, prueba que el flujo del firmware (config por MAC, lectura de
telemetria NDJSON, controlador, motores, paro seguro) corre sin errores de nombres
ni de logica. Corre con el simulador fisico como fuente de telemetria.
"""

import importlib
import json
import sys
import types

import pytest

from simulador_fisico import MundoSim

MAC_ROVER_1 = (224, 140, 254, 37, 199, 72)


class _Motor:
    def __init__(self):
        self.throttle = 0.0
        self.historial = []

    def __setattr__(self, k, v):
        if k == "throttle":
            self.__dict__.setdefault("historial", []).append(v)
        object.__setattr__(self, k, v)


def _instalar_fakes(monkeypatch, mundo_sim, max_mensajes):
    motores = {1: _Motor(), 2: _Motor()}
    leds = []
    pines_usados = []
    pines_led = []
    motores["pines_led"] = pines_led
    motores["leds"] = leds
    motores["pines_usados"] = pines_usados

    board = types.ModuleType("board")
    board.__getattr__ = lambda nombre: nombre  # board.IO26 -> "IO26"

    hcsr04 = types.ModuleType("hcsr04")
    hcsr04.HCSR04 = lambda trig, echo: types.SimpleNamespace(dist_cm=lambda: 50.0)

    ideaboard = types.ModuleType("ideaboard")

    class IdeaBoard:
        instancias = 0

        def __init__(self):
            # Como en el hardware real: una 2a instancia falla por pines PWM en uso.
            IdeaBoard.instancias += 1
            if IdeaBoard.instancias > 1:
                raise RuntimeError("pin in use (IdeaBoard creada dos veces)")
            self.motor_1, self.motor_2 = motores[1], motores[2]

        def DigitalIn(self, pin, pull=None):
            pines_usados.append(pin)
            return types.SimpleNamespace(value=False)

    ideaboard.IdeaBoard = IdeaBoard

    neopixel = types.ModuleType("neopixel")

    class NeoPixel:
        """Fake: guarda cada color escrito y falla si el pin ya esta en uso por otro."""

        def __init__(self, pin, n, brightness=1.0, auto_write=True):
            self.pin = pin
            pines_led.append(pin)
            self._c = [(0, 0, 0)] * n

        def __setitem__(self, i, color):
            self._c[i] = color
            if color != (0, 0, 0):
                leds.append(color)

        def __getitem__(self, i):
            return self._c[i]

    neopixel.NeoPixel = NeoPixel

    wifi = types.ModuleType("wifi")
    wifi.radio = types.SimpleNamespace(
        mac_address=bytes(MAC_ROVER_1), connect=lambda ssid, pw: None
    )

    cola = []

    class Sock:
        def connect(self, addr):
            pass

        def setblocking(self, b):
            pass

        def recv_into(self, buf):
            if len(cola) >= max_mensajes:
                raise KeyboardInterrupt  # termina el loop de main()
            msg = mundo_sim.mensaje()
            mundo_sim.paso({})
            cola.append(msg)
            datos = (json.dumps(msg) + "\n").encode()
            buf[: len(datos)] = datos
            return len(datos)

        def close(self):
            pass

    socketpool = types.ModuleType("socketpool")
    socketpool.SocketPool = lambda radio: types.SimpleNamespace(
        AF_INET=2, SOCK_STREAM=1, socket=lambda *a: Sock()
    )

    for nombre, mod in (("board", board), ("hcsr04", hcsr04), ("ideaboard", ideaboard),
                        ("neopixel", neopixel), ("wifi", wifi), ("socketpool", socketpool)):
        monkeypatch.setitem(sys.modules, nombre, mod)
    for nombre in [n for n in sys.modules if n == "firmware" or n.startswith("firmware.")]:
        monkeypatch.delitem(sys.modules, nombre)
    return motores, cola


def test_config_identifica_al_rover_por_mac(monkeypatch):
    _instalar_fakes(monkeypatch, MundoSim(), 1)
    config = importlib.import_module("firmware.config")
    assert config.MI_ARUCO_ID == 10
    assert config.IDS_ROVERS == [10, 11]
    assert config.MAC_OTRO_ROVER == bytes((224, 140, 254, 39, 166, 120))


def test_main_mueve_los_motores_y_termina_frenado(monkeypatch):
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y", "VISION_HOST": "127.0.0.1"}
    monkeypatch.setattr("os.getenv", lambda k, d=None: os_env.get(k, d))
    motores, cola = _instalar_fakes(monkeypatch, MundoSim(), 60)
    main = importlib.import_module("firmware.main")
    with pytest.raises(KeyboardInterrupt):
        main.main()
    assert len(cola) == 60
    hist1 = motores[1].historial
    assert any(abs(v) > 0.1 for v in hist1), "el rover nunca intento moverse"
    assert motores[1].throttle == 0.0 and motores[2].throttle == 0.0  # finally: frenados


def test_main_no_mueve_en_fase_ready(monkeypatch):
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y", "VISION_HOST": "127.0.0.1"}
    monkeypatch.setattr("os.getenv", lambda k, d=None: os_env.get(k, d))
    sim = MundoSim()
    sim_msg = sim.mensaje
    sim.mensaje = lambda *a, **k: sim_msg(phase="READY")
    motores, _ = _instalar_fakes(monkeypatch, sim, 30)
    main = importlib.import_module("firmware.main")
    with pytest.raises(KeyboardInterrupt):
        main.main()
    assert all(abs(v) < 1e-9 for v in motores[1].historial + motores[2].historial)


def test_main_exige_vision_host(monkeypatch):
    monkeypatch.setattr("os.getenv", lambda k, d=None: None)
    motores, _ = _instalar_fakes(monkeypatch, MundoSim(), 5)
    main = importlib.import_module("firmware.main")
    with pytest.raises(RuntimeError, match="VISION_HOST"):
        main.main()
    assert motores[1].throttle == 0.0 and motores[2].throttle == 0.0


def test_factor_de_velocidad_limita_la_potencia(monkeypatch):
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y", "VISION_HOST": "127.0.0.1"}
    monkeypatch.setattr("os.getenv", lambda k, d=None: os_env.get(k, d))
    motores, _ = _instalar_fakes(monkeypatch, MundoSim(), 80)
    config = importlib.import_module("firmware.config")
    config.FACTOR_VELOCIDAD = 0.3
    main = importlib.import_module("firmware.main")
    with pytest.raises(KeyboardInterrupt):
        main.main()
    movimiento = [abs(v) for v in motores[1].historial + motores[2].historial if abs(v) > 0.05]
    assert movimiento, "el rover nunca intento moverse"
    # Avance/empuje escalados por 0.3; los giros en el sitio (w_max 0.6) quedan fuera del factor.
    assert max(movimiento) <= 0.6 + 1e-9


def test_led_muestra_conexion_y_estado_del_rover(monkeypatch):
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y", "VISION_HOST": "127.0.0.1"}
    monkeypatch.setattr("os.getenv", lambda k, d=None: os_env.get(k, d))
    motores, _ = _instalar_fakes(monkeypatch, MundoSim(), 60)
    main = importlib.import_module("firmware.main")
    colores = importlib.import_module("firmware.indicador").COLORES
    with pytest.raises(KeyboardInterrupt):
        main.main()
    leds = motores["leds"]
    assert leds[0] == colores["conectando"][0]
    assert colores["esperando"][0] in leds
    assert colores["APROXIMAR"][0] in leds  # RUNNING: muestra el estado del FSM


def test_led_rojo_si_falta_la_configuracion(monkeypatch):
    monkeypatch.setattr("os.getenv", lambda k, d=None: None)
    motores, _ = _instalar_fakes(monkeypatch, MundoSim(), 5)
    main = importlib.import_module("firmware.main")
    colores = importlib.import_module("firmware.indicador").COLORES
    with pytest.raises(RuntimeError):
        main.main()
    assert motores["leds"][-1] == colores["error"][0]


def test_led_en_io33_y_sin_choque_con_otros_pines(monkeypatch):
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y", "VISION_HOST": "127.0.0.1"}
    monkeypatch.setattr("os.getenv", lambda k, d=None: os_env.get(k, d))
    motores, _ = _instalar_fakes(monkeypatch, MundoSim(), 10)
    main = importlib.import_module("firmware.main")
    with pytest.raises(KeyboardInterrupt):
        main.main()
    assert motores["pines_led"] == ["IO33"]          # el LED que responde en los rovers
    assert "IO33" not in motores["pines_usados"]     # ningun otro periferico usa ese pin


def test_indicador_parpadeos_con_reloj_falso(monkeypatch):
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y", "VISION_HOST": "127.0.0.1"}
    monkeypatch.setattr("os.getenv", lambda k, d=None: os_env.get(k, d))
    motores, _ = _instalar_fakes(monkeypatch, MundoSim(), 1)
    ind_mod = importlib.import_module("firmware.indicador")
    t = [100.0]
    ind = ind_mod.Indicador(reloj=lambda: t[0])

    def color_actual():
        return ind._np[0]

    # fijo: siempre encendido
    ind.mostrar("TRANSPORTAR")
    for dt in (0.0, 0.3, 0.7, 5.0):
        t[0] = 100.0 + dt
        ind.actualizar()
        assert color_actual() == ind_mod.VERDE
    # lento (1 Hz): encendido 0-0.5 s, apagado 0.5-1.0 s
    t[0] = 200.0
    ind.mostrar("APROXIMAR")
    assert color_actual() == ind_mod.VERDE          # al cambiar, empieza encendido
    t[0] = 200.6
    ind.actualizar()
    assert color_actual() == (0, 0, 0)
    t[0] = 201.1
    ind.actualizar()
    assert color_actual() == ind_mod.VERDE
    # rapido (4 Hz): encendido 0-0.125 s, apagado 0.125-0.25 s
    t[0] = 300.0
    ind.mostrar("SUJETAR")
    t[0] = 300.2
    ind.actualizar()
    assert color_actual() == (0, 0, 0)
    t[0] = 300.26
    ind.actualizar()
    assert color_actual() == ind_mod.VERDE


def test_paleta_no_depende_del_rojo_mezclado():
    # el rojo solo se usa puro (ROJO); ningun otro color lo mezcla con verde/azul salvo el blanco
    import importlib
    import sys
    sys.modules.setdefault("board", __import__("types").ModuleType("board"))
    sys.modules.setdefault("neopixel", __import__("types").ModuleType("neopixel"))
    from_mod = importlib.import_module("firmware.indicador")
    for clave, (color, _) in from_mod.COLORES.items():
        r, g, b = color
        assert r == 0 or color in (from_mod.ROJO, from_mod.BLANCO), clave
    # y todos los estados del FSM y de conexion tienen una senal distinta (color, patron)
    assert len(set(from_mod.COLORES.values())) == len(from_mod.COLORES)
