"""Buffer NDJSON: corta por newline y se queda con el ultimo JSON v=2."""
import json
BUF_MAX = 8192
PROTOCOLO_V = 2

class BufferNDJSON:
    def __init__(self):
        self._buf = bytearray()
        self._ultimo = None

    def alimentar(self, trozo):
        """Acumula bytes, parsea líneas completas y conserva el último v==2."""
        if trozo:
            self._buf.extend(trozo)
        while True:
            n = self._buf.find(b"\n")
            if n < 0:
                break
            linea = bytes(self._buf[:n])
            self._buf = bytearray(self._buf[n + 1 :])
            if not linea.strip():
                continue
            try:
                obj = json.loads(linea.decode("utf-8"))
            except (UnicodeError, ValueError, TypeError):
                continue
            if isinstance(obj, dict) and obj.get("v") == PROTOCOLO_V:
                self._ultimo = obj
        if len(self._buf) > BUF_MAX:
            self._buf = bytearray()
        return self._ultimo

    def ultimo(self):
        return self._ultimo

    def limpiar(self):
        """Al caer el socket: ni el trozo partido ni el JSON viejo sirven."""
        self._buf = bytearray()
        self._ultimo = None
