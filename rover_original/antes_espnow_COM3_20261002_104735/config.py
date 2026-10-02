"""Compatibilidad con el import config del transporte suministrado."""
import os
WIFI_SSID = os.getenv("Jcgarage")
WIFI_PASSWORD = os.getenv("JeJbp12603*1307#")
VISION_HOST = os.getenv("192.168.1.13")
VISION_PORT = os.getenv("VISION_PORT") or 2026
