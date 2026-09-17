"""Se ejecuta una sola vez al encender el ESP32, antes de main.py.

Por ahora solo deja el import path listo. TODO: cuando se decida si se usa
NTP para acercar el reloj local al de la vision (no es obligatorio -- ver
docs/contrato_telemetria.md, la latencia se mide como variacion, no en
absoluto), inicializarlo aca.
"""

import sys

# En MicroPython el filesystem del ESP32 suele montarse en /, y comun/ se copia
# junto a firmware/ al dispositivo (ver firmware/README.md). Si el layout de
# archivos en el device difiere del repo, ajustar este path.
if "/comun" not in sys.path:
    sys.path.append("/")
