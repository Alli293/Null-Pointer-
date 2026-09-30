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

    board = types.ModuleType("board")
    board.__getattr__ = lambda nombre: nombre  # board.IO26 -> "IO26"

    hcsr04 = types.ModuleType("hcsr04")
    hcsr04.HCSR04 = lambda trig, echo: types.SimpleNamespace(dist_cm=lambda: 50.0)

    ideaboard = types.ModuleType("ideaboard")

    class IdeaBoard:
        def __init__(self):
            self.motor_1, self.motor_2 = motores[1], motores[2]

        def DigitalIn(self, pin, pull=None):
            return types.SimpleNamespace(value=False)

    ideaboard.IdeaBoard = IdeaBoard

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
                        ("wifi", wifi), ("socketpool", socketpool)):
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
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y"}
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
    os_env = {"CIRCUITPY_WIFI_SSID": "x", "CIRCUITPY_WIFI_PASSWORD": "y"}
    monkeypatch.setattr("os.getenv", lambda k, d=None: os_env.get(k, d))
    sim = MundoSim()
    sim_msg = sim.mensaje
    sim.mensaje = lambda *a, **k: sim_msg(phase="READY")
    motores, _ = _instalar_fakes(monkeypatch, sim, 30)
    main = importlib.import_module("firmware.main")
    with pytest.raises(KeyboardInterrupt):
        main.main()
    assert all(abs(v) < 1e-9 for v in motores[1].historial + motores[2].historial)
