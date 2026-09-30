"""Constantes y validaciones del contrato de telemetria del sistema de vision.

Ver docs/contrato_telemetria.md para el detalle completo. Este modulo NO usa nada
fuera de la libreria estandar minima (dict/list/str/int) para poder correr igual en
CPython (PC, tests) y en MicroPython (ESP32).
"""

# Version de protocolo que este equipo sabe interpretar. Si llega un mensaje con otra
# version hay que descartarlo (Regla 6.5 del contrato: formato desconocido).
#
# El repo guia paso de v1 a v2 (sumo `clock`, `depot_size`, `cube_side`, y movio
# `start` para que ya NO coincida con el origen). Ver docs/contrato_telemetria.md.
VERSION_SOPORTADA = 2

# Fases de una ronda, tal como las publica el sistema de vision.
FASE_IDLE = "IDLE"
FASE_READY = "READY"
FASE_RUNNING = "RUNNING"
FASE_FINISHED = "FINISHED"

# Colores validos de cubo/depot (maximo un cubo por color en toda la cancha).
COLORES = ("red", "green", "blue")

# Umbrales de frescura para age_ms (Regla 2: age_ms alto es oclusion, no
# desaparicion). Estos valores son un punto de partida razonable, no un numero
# oficial del contrato -- ajustar con datos reales de la camara/cancha.
UMBRAL_FRESCO_MS = 200
UMBRAL_DUDOSO_MS = 1500

# Umbral de "variacion de latencia" (ver docs/contrato_telemetria.md: no se mide en
# absoluto porque el contrato no garantiza reloj sincronizado). Si el offset crece
# mas que esto respecto a la primera muestra, tratamos el mensaje como demasiado
# viejo para tomar decisiones de movimiento.
UMBRAL_VARIACION_LATENCIA_MS = 500

# Etiquetas de frescura que devuelve mundo.clasificar_frescura().
FRESCO = "fresco"
DUDOSO = "dudoso"
NO_CONFIABLE = "no_confiable"


def validar_version(msg):
    """True si el mensaje trae una version de protocolo que sabemos leer."""
    return isinstance(msg, dict) and msg.get("v") == VERSION_SOPORTADA


def es_color_valido(color):
    return color in COLORES
