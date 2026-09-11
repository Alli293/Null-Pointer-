"""Hace que `comun/` (en la raiz del repo) sea importable al correr pytest
desde pc_dev/, sin instalar el proyecto como paquete."""

import os
import sys

_RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _RAIZ_REPO not in sys.path:
    sys.path.insert(0, _RAIZ_REPO)
