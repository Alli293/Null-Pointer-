"""Coordinacion de dos placas: MAC mayor lidera; planes exclusivos por tandas.

Sin hardware ni reloj global. El tercer cubo espera a que ambos terminen la
primera tanda, para comparar sus posiciones actuales sin interrumpir empujes.
"""
from comun import mundo

TIMEOUT_RADIO_MS = 750


def mac48(mac):
    if len(mac) != 6 or any(not 0 <= b <= 255 for b in mac):
        raise ValueError("MAC debe contener seis bytes")
    valor = 0
    for b in mac:
        valor = (valor << 8) | b
    return valor


def entregado(msg, cubo):
    depot = mundo.depot_por_color(msg, cubo["color"])
    return (mundo.es_fresco(cubo) and depot is not None and
            mundo.cubo_en_su_zona(cubo, depot, msg["depot_size"],
                                 msg["grid"], msg["cube_side"])[0])


def repartir(msg, ids):
    """Par rover-cubo mas cercano primero; desempate por ID y color."""
    rovers = [mundo.mi_rover(msg, rid) for rid in ids]
    if any(r is None or not mundo.es_fresco(r) for r in rovers):
        return [None for _ in ids]
    cubos = [c for c in msg["cubes"] if mundo.es_fresco(c)
             and mundo.depot_por_color(msg, c["color"]) is not None
             and not entregado(msg, c)]
    pares = sorted((mundo.distancia(r, c), r["id"], c["color"])
                   for r in rovers for c in cubos)
    asignados = {}
    usados = set()
    for _, rid, color in pares:
        if rid not in asignados and color not in usados:
            asignados[rid] = color
            usados.add(color)
    return [asignados.get(rid) for rid in ids]


class Coordinador:
    def __init__(self, mac, otro_mac, ids, mi_id, sesion):
        self.mac = mac48(mac)
        self.otro = mac48(otro_mac)
        self.lider = self.mac > self.otro
        self.ids = sorted(ids)
        self.indice = self.ids.index(mi_id)
        self.sesion = sesion
        self.peer = None
        self.ultimo_rx = None
        self.numero_rx = -1
        self.numero_tx = 0
        self.revision = 0
        self.plan = [None, None]

    def recibir(self, p, ahora):
        if not isinstance(p, dict) or p.get("v") != 1 or p.get("mac") != self.otro:
            return
        if not isinstance(p.get("s"), str) or not isinstance(p.get("n"), int):
            return
        plan = p.get("p")
        if (not isinstance(plan, list) or len(plan) != 2 or
                any(c not in (None, "red", "green", "blue") for c in plan) or
                (plan[0] is not None and plan[0] == plan[1]) or
                not isinstance(p.get("r"), int)):
            return
        if self.peer is None or p["s"] != self.peer["s"]:
            self.numero_rx = -1
            # Nueva placa/sesion: retirar cualquier encargo anterior.
            self.plan = [None, None]
            self.revision = self.revision + 1 if self.lider else 0
        if p["n"] <= self.numero_rx:
            return
        self.peer = p
        self.numero_rx = p["n"]
        self.ultimo_rx = ahora
        if not self.lider and p.get("to") == self.sesion and p["r"] >= self.revision:
            self.plan = list(plan)
            self.revision = p["r"]

    def conectado(self, ahora):
        return (self.peer is not None and self.ultimo_rx is not None and
                ahora - self.ultimo_rx < TIMEOUT_RADIO_MS and
                self.peer.get("to") == self.sesion)

    def actualizar(self, msg, ahora, terminado):
        if self.lider and msg["phase"] != "RUNNING":
            if any(self.plan):
                self.plan = [None, None]
                self.revision += 1
        if self.lider and msg["phase"] == "RUNNING" and self.conectado(ahora):
            confirmado = self.peer.get("r") == self.revision
            libres = terminado and self.peer.get("done") is True
            if confirmado and libres:
                nuevo = repartir(msg, self.ids)
                if nuevo != self.plan:
                    self.plan = nuevo
                    self.revision += 1

    def mensaje(self, terminado):
        self.numero_tx += 1
        return {"v": 1, "mac": self.mac, "s": self.sesion,
                "to": self.peer["s"] if self.peer else "", "n": self.numero_tx,
                "r": self.revision, "p": self.plan, "done": bool(terminado)}

    def autorizado(self, ahora):
        return (self.conectado(ahora) and
                (not self.lider or self.peer.get("r") == self.revision))
