import importlib
import sys
import types
import pytest
from firmware.buffer_ndjson import BufferNDJSON


def test_buffer_fragmentos_y_version():
    b = BufferNDJSON()
    assert b.alimentar(b'{"v":') is None
    assert b.alimentar(b'2,"seq":1}\n{"v":3}\ninvalid\n[]\n')["seq"] == 1
    assert b.alimentar(b'{"v":2,"seq":2}\n{"v":2,"seq":3}\n')["seq"] == 3
    b.alimentar(b'x' * 8193)
    assert not b._buf
    assert b.ultimo()["seq"] == 3
    b.limpiar()
    assert b.ultimo() is None


def adapter(monkeypatch):
    from test_firmware_main import _instalar_fakes
    from simulador_fisico import MundoSim
    _instalar_fakes(monkeypatch, MundoSim(), 20)
    mod = importlib.import_module("firmware.comm_vision")
    monkeypatch.setattr(mod.tcp, "abrir_tcp", lambda pool: object())
    monkeypatch.setattr(mod.tcp, "cerrar", lambda sock: None)
    t = [0.0]
    monkeypatch.setattr(mod.time, "monotonic", lambda: t[0])
    c = mod.ClienteVision("127.0.0.2", 2026)
    c.conectar()
    return mod, c, t


def test_watchdog_no_renueva_por_json_repetido(monkeypatch):
    mod, c, t = adapter(monkeypatch)
    def drain(sock, buf):
        buf.alimentar(b'{"v":2,"seq":1}\n')
        return True
    monkeypatch.setattr(mod.tcp, "drenar_tcp", drain)
    assert c.leer_ultimo_mensaje()["seq"] == 1
    t[0] = 0.5
    assert c.leer_ultimo_mensaje() is None
    t[0] = 0.75
    with pytest.raises(OSError):
        c.leer_ultimo_mensaje()
    assert c._buf.ultimo() is None and c._sock is None


def test_error_tcp_limpia_buffer(monkeypatch):
    mod, c, t = adapter(monkeypatch)
    c._buf.alimentar(b'{"v":2,"seq":4}\n')
    monkeypatch.setattr(mod.tcp, "drenar_tcp", lambda sock, buf: False)
    with pytest.raises(OSError):
        c.leer_ultimo_mensaje()
    assert c._buf.ultimo() is None


def test_reintento_mantiene_motores_detenidos(monkeypatch):
    from test_firmware_main import _instalar_fakes
    from simulador_fisico import MundoSim
    _instalar_fakes(monkeypatch, MundoSim(), 1)
    mod = importlib.import_module("firmware.main")
    eventos = []
    def conectar():
        eventos.append("connect")
        if eventos.count("connect") == 1:
            raise OSError(119, "EINPROGRESS")
    monkeypatch.setattr("time.sleep", lambda t: eventos.append("sleep"))
    mod.conectar_vision(types.SimpleNamespace(host="host", port=2026, conectar=conectar),
        types.SimpleNamespace(detener=lambda: eventos.append("stop")),
        types.SimpleNamespace(mostrar=lambda estado: None))
    assert eventos == ["stop", "connect", "sleep", "stop", "connect"]
