"""Configuracion puente para el transporte TCP del usuario.

Acepta settings.toml de CircuitPython y secrets.py local. Nunca guardar claves
reales en este archivo ni subir secrets.py.
"""
import os

try:
    import secrets as _secrets
except ImportError:
    _secrets = None


def _valor(nombre_ambiente, nombres_secret, default=None):
    # Los valores configurados explícitamente en secrets.py prevalecen sobre
    # cualquier valor antiguo que haya quedado en settings.toml.
    if _secrets is not None:
        for nombre in nombres_secret:
            valor = getattr(_secrets, nombre, None)
            if valor:
                return valor
    valor = os.getenv(nombre_ambiente)
    return valor if valor else default


WIFI_SSID = _valor("CIRCUITPY_WIFI_SSID", ("WIFI_SSID", "SSID", "ssid"), "CAMBIAR")
WIFI_PASSWORD = _valor("CIRCUITPY_WIFI_PASSWORD", ("WIFI_PASSWORD", "PASSWORD", "password"), "")
VISION_HOST = _valor("VISION_HOST", ("VISION_HOST", "vision_host"))
VISION_PORT = _valor("VISION_PORT", ("VISION_PORT", "vision_port"), 2026)
