import gc
import select
import time

import config

try:
    import wifi
    import socketpool
except ImportError:
    wifi = None
    socketpool = None

# CircuitPython/ESP-IDF: el primer connect() tira 119. El segundo, mientras
# el handshake sigue, tira 128 y no 120. Cortar ahi deja la vision arriba
# y el robot pasando al host siguiente.
EINPROGRESS = 119
EALREADY = 120
EISCONN = 127
ENOTCONN = 128
_EN_CURSO = (EINPROGRESS, EALREADY, ENOTCONN)
CONECTAR_S = 5.0

RX = bytearray(512)
# recv sin datos en un socket no bloqueante. Cualquier otro errno es el
# cable muerto: si se traga, el robot se queda con el ultimo JSON para siempre.
_SIN_DATOS = (11, 35, 116)
_CACHE_HOST = "/vision_ok.txt"
_ultimo_ok = None
_scan_i = 0
_cache_leido = False
_arranque = b""


def conectar_wifi():
    if wifi is None:
        return False
    ssid = config.WIFI_SSID
    if not ssid or ssid == "CAMBIAR":
        print("WIFI_SSID=CAMBIAR: copia secrets.py.example a secrets.py")
        return False
    try:
        if not wifi.radio.ipv4_address:
            print("Wi-Fi a", ssid)
            # Escanear antes y cerrar el scan hace que connect() responda
            # "No network with that ssid" aunque la red este en el canal 10.
            wifi.radio.connect(ssid, config.WIFI_PASSWORD, timeout=15)
        print("Wi-Fi IP", wifi.radio.ipv4_address)
        # El modem-sleep del ESP32 tira el UDP y connect() lo reporta como
        # (-2, 'Name or service not known') aunque el DNS del DHCP exista.
        try:
            wifi.radio.power_management = wifi.PowerManagement.NONE
        except Exception:
            pass
        return bool(wifi.radio.ipv4_address)
    except Exception as err:
        print("Wi-Fi fallo:", err)
        return False


def _leer_cache():
    global _ultimo_ok, _cache_leido
    if _cache_leido:
        return
    _cache_leido = True
    try:
        linea = open(_CACHE_HOST, "r").read().strip()
    except OSError:
        return
    if linea and linea[0].isdigit():
        _ultimo_ok = linea.split()[0]


def _guardar_cache(host):
    global _ultimo_ok
    _ultimo_ok = host
    try:
        f = open(_CACHE_HOST, "w")
        f.write(host + "\n")
        f.close()
    except OSError:
        pass


def _yo_ip():
    if wifi is None or not wifi.radio.ipv4_address:
        return None
    return str(wifi.radio.ipv4_address)


def _candidatos():
    _leer_cache()
    yo = _yo_ip()
    ordered = []

    def add(host):
        if not host or host in ordered:
            return
        if host in ("127.0.0.1", "localhost"):
            return
        if yo is not None and host == yo:
            return
        ordered.append(host)

    add(config.VISION_HOST)
    add(_ultimo_ok)
    if yo is not None:
        partes = yo.split(".")
        if len(partes) == 4:
            # Laboratorios es /22: 41.x y 42.x. El scan .41.2-.39 no es la laptop.
            vis = str(config.VISION_HOST or "").split(".")
            if len(vis) == 4:
                add("%s.%s.%s.%s" % (partes[0], partes[1], vis[2], vis[3]))
                add("%s.%s.%s.%s" % (partes[0], partes[1], partes[2], vis[3]))
            prefijo = ".".join(partes[:3])
            for n in range(2, 40):
                add("%s.%d" % (prefijo, n))
    return ordered


def _conectar_host(pool, host, puerto):
    sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    try:
        # Un solo connect() bloqueante. En 9.2.4 el propio connect() espera
        # el timeout. Llamarlo otra vez, con el handshake vivo, tira
        # (-2, 'Name or service not known').
        sock.settimeout(CONECTAR_S)
        sock.connect((host, puerto))
        # recv no bloqueante a veces devuelve 0 con datos ya en camino.
        # Una lectura corta aqui deja la primera linea antes del watchdog.
        global _arranque
        _arranque = b""
        # La linea pasa de 512 bytes. Una sola lectura deja el JSON partido
        # y el watchdog corta antes de ver phase.
        partes = []
        sock.settimeout(0.15)
        limite = time.monotonic() + 0.6
        while time.monotonic() < limite:
            try:
                n = sock.recv_into(RX)
            except OSError:
                break
            if not n:
                time.sleep(0.02)
                continue
            partes.append(bytes(RX[:n]))
            if b"\n" in partes[-1]:
                break
        if partes:
            _arranque = b"".join(partes)
        # setblocking(False) en esta placa hace que recv devuelva 0
        # aunque lleguen lineas. Un timeout corto si lee lo que entra.
        sock.settimeout(0.05)
        return sock
    except Exception as err:
        try:
            sock.close()
        except Exception:
            pass
        raise err


def abrir_tcp(pool):
    global _scan_i
    # simple.py llena el heap. Sin este collect, ping y getaddrinfo tiran
    # Out of memory y el -2 de 'Name or service not known'.
    gc.collect()
    gc.collect()
    puerto = int(config.VISION_PORT)
    cands = _candidatos()
    if not cands:
        print("VISION_HOST no puede ser 127.0.0.1; usa la IP de la laptop")
        return None
    # La IP de la visión va primero en cada intento. Si se avanzaba el índice
    # al conectar, la caída siguiente probaba .2, .3, .4… y la ronda seguía
    # unos tres minutos sin ninguno de los dos adentro.
    orden = [cands[0]]
    extra = cands[_scan_i % len(cands)]
    if extra not in orden:
        orden.append(extra)
    for host in orden:
        try:
            sock = _conectar_host(pool, host, puerto)
        except Exception as err:
            print("TCP fallo {}: {}".format(host, err))
            # -2 es el heap, no un host equivocado. Barrer .2–.39 deja
            # los motores en cero un buen rato.
            if "-2" in str(err) or "emory" in str(err):
                return None
            continue
        _guardar_cache(host)
        _scan_i = 0
        print("TCP {}:{}".format(host, puerto))
        return sock
    _scan_i = (_scan_i + 1) % len(cands)
    return None


def drenar_tcp(sock, buf):
    """True si el socket sigue vivo. False si hay que reconectar.

    La lectura de arranque entra antes del bucle: si no, el primer
    recv no bloqueante ve 0 y el watchdog corta una linea que ya venia.

    En la IdeaBoard, recv_into sin bytes a veces tira EAGAIN y a veces
    devuelve 0 o None. Tratar eso como cable muerto cerraba el socket
    despues de leer el JSON y lo tiraba con limpiar(), antes de mover.
    El cierre de verdad lo ve el watchdog: 0.75 s sin seq nuevo.
    """
    global _arranque
    if _arranque and buf is not None:
        buf.alimentar(_arranque)
        _arranque = b""
    while True:
        try:
            n = sock.recv_into(RX)
        except OSError as err:
            if getattr(err, "errno", None) in _SIN_DATOS:
                return True
            return False
        if n is None or n == 0:
            return True
        if buf is not None:
            buf.alimentar(bytes(RX[:n]))


def cerrar(sock):
    if sock is None:
        return None
    try:
        sock.close()
    except Exception:
        pass
    return None