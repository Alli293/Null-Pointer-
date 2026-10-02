"""Respalda y verifica byte a byte el firmware; deja la placa en REPL, sin moverla."""
import base64
import datetime
import json
from pathlib import Path
import sys

import _rover

ROOT = Path(__file__).resolve().parents[1]
MACS = {"COM3": [224, 140, 254, 37, 199, 72],
        "COM4": [224, 140, 254, 39, 166, 120]}


def ejecutar(port, code):
    status, result = _rover.mpremote(port, "exec", code)
    if status:
        raise RuntimeError(result)
    return result


def main(port, rover=None):
    _rover.interrumpir(port)
    identity = json.loads(ejecutar(port,
        "import wifi,json; print(json.dumps(list(wifi.radio.mac_address)))"))
    esperada = MACS["COM3" if rover == "1" else "COM4"] if rover else MACS[port]
    if identity != esperada:
        raise RuntimeError("MAC no coincide con la placa esperada")
    files = {str(p.relative_to(ROOT)).replace("\\", "/"): p
             for folder in ("comun", "firmware")
             for p in sorted((ROOT / folder).glob("*.py")) if p.name != "code.py"}
    files["code.py"] = ROOT / "firmware" / "code.py"
    files["config.py"] = ROOT / "config.py"
    if (ROOT / "secrets.py").exists():
        files["secrets.py"] = ROOT / "secrets.py"
    read_code = "import json,binascii,gc\n"
    read_code += "for path in %r:\n" % list(files)
    read_code += ("    try:\n"
                  "        with open('/'+path,'rb') as f:\n"
                  "            data=binascii.b2a_base64(f.read()).decode().strip()\n"
                  "    except OSError as e:\n"
                  "        if e.args[0] != 2: raise\n"
                  "        data=None\n"
                  "    print(json.dumps([path,data]))\n"
                  "    del data\n"
                  "    gc.collect()\n")
    previous = dict(json.loads(line) for line in ejecutar(port, read_code).splitlines() if line.strip())
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ROOT / "rover_original" / ("antes_espnow_" + port + "_" + stamp)
    backup.mkdir(parents=True)
    for path, data in previous.items():
        if data is not None:
            dest = backup / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(base64.b64decode(data))
    (backup / "manifest.json").write_text(json.dumps({
        "port": port, "mac": identity, "missing": [p for p, d in previous.items() if d is None]
    }, indent=2))
    print("RESPALDO", backup, flush=True)
    for path, local in files.items():
        ok, result = _rover.subir(port, str(local), path)
        if not ok:
            raise RuntimeError(path + ": " + result)
        print("COPIADO", port, path, flush=True)
    actual = dict(json.loads(line) for line in ejecutar(port, read_code).splitlines() if line.strip())
    for path, local in files.items():
        expected = local.read_bytes().replace(b"\r\n", b"\n")
        if actual[path] is None or base64.b64decode(actual[path]) != expected:
            raise RuntimeError("Verificacion fallo: " + path)
    print("VERIFICADOS", port, len(files), "archivos identicos", flush=True)
    print(ejecutar(port, "import firmware.main; print('IMPORTACION OK')"), flush=True)
    print("Placa en REPL; reiniciar para ejecutar code.py", flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("puerto")
    parser.add_argument("--rover", choices=("1", "2"), help="Identidad esperada, independiente del puerto USB")
    args = parser.parse_args()
    main(args.puerto, args.rover)
