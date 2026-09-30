# Null-Pointer — Vision Rover Challenge

Proyecto del equipo para el [Vision Rover Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge)
de Cenfotec: dos CenfoBot (IdeaBoard ESP32, **CircuitPython**) deben ubicar, transportar y
depositar cubos de color en su zona, coordinándose entre sí, guiados por un sistema de
visión externo que **solo da percepción** (posición y orientación). Toda la decisión corre
a bordo de los rovers, sin PC externa durante la ronda.

> **Estado al 30-sep-2026:** la lógica completa está hecha y verificada **en simulación**
> (57 tests; los 2 rovers entregan los 3 cubos en ~30 s simulados). **Nada corrió todavía
> en los rovers reales con la cámara.** Lo que sí se probó en hardware: lectura de los
> rovers por USB, mapeo de motores y mensajes ESP-NOW entre los dos. El plan para dar el
> salto a la prueba real está en la [sección 7](#7-plan-paso-a-paso-hasta-la-prueba-real).

## Índice

1. [Mapa del repositorio](#1-mapa-del-repositorio)
2. [Lo que se hizo](#2-lo-que-se-hizo)
3. [Los rovers: hardware y datos medidos](#3-los-rovers-hardware-y-datos-medidos)
4. [Cómo nos conectamos a los rovers](#4-cómo-nos-conectamos-a-los-rovers)
5. [Simulación y tests](#5-simulación-y-tests)
6. [Lo que falta por hacer](#6-lo-que-falta-por-hacer)
7. [Plan paso a paso hasta la prueba real](#7-plan-paso-a-paso-hasta-la-prueba-real)
8. [Problemas conocidos y soluciones](#8-problemas-conocidos-y-soluciones)
9. [Flujo de trabajo con git](#9-flujo-de-trabajo-con-git)
10. [Referencias](#10-referencias)

---

## 1. Mapa del repositorio

| Carpeta | Dónde corre | Qué contiene |
|---|---|---|
| [`comun/`](comun/) | **PC y rover** (mismo código) | Toda la decisión. `contrato.py` (constantes), `mundo.py` (emparejar por identidad, frescura, latencia), `maquina_estados.py` (FSM), `navegacion.py` (geometría y control de rumbo), `planificador.py` (a dónde ir según el estado), `rover.py` (`ControladorRover`: FSM + planificador + reparto de colores + cesión de paso), `protocolo_rovers.py` (mensajes inter-rover y reparto estático). No usa nada que no exista en CircuitPython. |
| [`firmware/`](firmware/) | Solo rover (CircuitPython) | Lo que toca hardware: `motores.py`, `sensores.py`, `comm_vision.py` (TCP), `comm_espnow.py`, `config.py` (identidad por MAC), `main.py` (loop), `code.py` (punto de entrada), `settings.toml.example`. |
| [`pc_dev/`](pc_dev/) | Solo PC | `simulador_fisico.py` (lazo cerrado), `ejecutar_simulacion.py` (contra un publisher real/mock), `trazar_simulacion.py` (depuración), `tests/` (pytest). |
| [`herramientas/`](herramientas/) | PC, habla con los rovers por USB | `info_rover.py`, `respaldar_rover.py`, `probar_motores.py`, `desplegar.py`. Ver [sección 4](#4-cómo-nos-conectamos-a-los-rovers). |
| [`rover_original/`](rover_original/) | — | Respaldo del contenido de fábrica de cada rover (`rover1/`, `rover2/`). Sirve para restaurarlos. |
| [`docs/`](docs/) | — | [`contrato_telemetria.md`](docs/contrato_telemetria.md) (protocolo v2) y [`arquitectura.md`](docs/arquitectura.md). |
| [`simulacion/`](simulacion/) | — | Cómo usar el `mock_publisher` del repo guía. |

**Idea central:** la lógica (`comun/`) se escribe una sola vez, se prueba con `pytest` en la
PC y se copia **sin cambios** al rover. Lo que funciona en simulación es lo que corre en el robot.

---

## 2. Lo que se hizo

Cronológico, en `develop` (PRs #1 a #5):

1. **Esqueleto inicial** (PR #1): `comun/`, `firmware/`, `pc_dev/`, docs y 24 tests.
2. **Protocolo de telemetría v2** (PR #2): `clock`, `depot_size`, `cube_side`, `start` distinto del
   origen, zonas de entrega como rectángulos. La entrega se verifica con la fórmula exacta del
   contrato (`mundo.cubo_en_su_zona`).
3. **Migración a CircuitPython** (PR #3): el esqueleto asumía MicroPython, pero los rovers traen
   **CircuitPython 9.2.4** (IdeaBoard de CRCibernetica). Se reescribió `firmware/` con `ideaboard`,
   `hcsr04`, `socketpool`/`wifi` y el módulo `espnow`. `comun/` no cambió.
4. **Identidad por MAC + respaldo del rover 2** (PR #4): un solo `config.py` sirve para los dos
   rovers; cada uno se reconoce por la MAC de su radio. Los IDs ArUco se decodificaron de fotos
   de los stickers.
5. **Navegación, planificador y simulador físico** (PR #5):
   - Estrategia: el cubo se **empuja** con el frente (entre las paletas). El rover se ubica
     detrás del cubo (lado opuesto al depot), avanza siguiendo la línea cubo→depot corrigiendo el
     desvío lateral, suelta cuando la visión confirma el cubo adentro de la zona (con 1 celda de
     margen), retrocede y pasa al siguiente color. Si el cubo se escapa, lo recupera.
   - FSM: umbral de agarre realista (6 celdas, no 1: el centro del rover nunca llega tan cerca),
     entrega por zona, recuperación de cubo perdido.
   - `ControladorRover.paso(msg, tiene_cubo)` devuelve `(izq, der)`; lo usan igual el firmware y
     el simulador. No se mueve fuera de la fase `RUNNING`; en `FINISHED` se detiene.
   - `firmware/main.py`: loop con paro de seguridad (sin telemetría por >500 ms, error o Ctrl-C →
     motores frenados).
6. **Herramientas y cabos sueltos** (este PR): scripts en `herramientas/`, `VISION_HOST` leído del
   `settings.toml`, mensajes de diagnóstico en `main.py`, `ejecutar_simulacion.py` usando el
   controlador real, este README.

**Hallazgos en hardware real** (ver [sección 3](#3-los-rovers-hardware-y-datos-medidos)):
los rovers no traían código de coordinación ni de sensores propio (solo el de fábrica de la
IdeaBoard y pruebas de LED/motores/I2C); `motor_1` es la rueda izquierda y `motor_2` la derecha,
ambos van hacia adelante con potencia positiva (sin invertir); ESP-NOW funciona en ambos sentidos
(5 de 5 mensajes, señal de −22 a −31 dBm a corta distancia).

---

## 3. Los rovers: hardware y datos medidos

| | Rover 1 | Rover 2 |
|---|---|---|
| Puerto USB (en esta PC) | `COM3` | `COM12` |
| ID ArUco (sticker) | **10** (diccionario 4X4) | **11** (diccionario 4X4) |
| MAC (radio WiFi / ESP-NOW) | `E0:8C:FE:25:C7:48` = `(224,140,254,37,199,72)` | `E0:8C:FE:27:A6:78` = `(224,140,254,39,166,120)` |
| UID placa | `0EC8EF527C84` | `0EC8EF726A87` |
| Firmware | CircuitPython 9.2.4, IdeaBoard | igual |
| Colores asignados (estático) | rojo, azul | verde |

> Los números de puerto pueden cambiar si se enchufan en otro orden o en otra PC; lo que
> identifica a cada rover es la MAC, y `firmware/config.py` la usa.

**Pines (código de fábrica de la IdeaBoard, en `rover_original/`):**

| Función | Pin / detalle |
|---|---|
| Motor 1 (**rueda izquierda**) | IO12 / IO14 |
| Motor 2 (**rueda derecha**) | IO13 / IO15 |
| Ultrasónico HCSR04 | TRIG IO26, ECHO IO25 |
| Infrarrojo | IO33 (ojo: el `code.py` de prueba de fábrica usa IO33 para un NeoPixel; confirmar cableado) |
| LED RGB | NeoPixel integrado (`board.NEOPIXEL`) |
| IMU | I2C, librería `adafruit_lsm6ds` |
| Sensor de color | I2C (Qwiic) — **aún sin integrar** |

Librerías ya instaladas en `/lib` de ambos rovers: `ideaboard`, `hcsr04`, `adafruit_motor`,
`adafruit_lsm6ds`, `neopixel`, `simpleio`, `adafruit_requests`, etc.

**Contenido de fábrica:** `code.py` (prueba del LED), `prueba.py` (LED + motores + I2C, idéntico
en ambos) y `examples/`. El `code.py` del rover 2 era solo `print('standby, sin wifi')` con un
bucle infinito (por eso `mpremote` no podía entrar sin Ctrl-C).

---

## 4. Cómo nos conectamos a los rovers

Desde la sesión de Claude Code (y desde cualquier terminal) se habla con los rovers **por el
cable USB**, sin Thonny, con **`mpremote`**, la herramienta oficial de MicroPython/CircuitPython.
Claude Code corre los comandos en la terminal de la PC; no hay nada "mágico".

### Preparación (una vez por PC)

```bash
pip install --user mpremote            # trae pyserial
python -m mpremote connect list        # lista los puertos (COM3, COM12...)
```

Siempre `python -m mpremote ...` (no `mpremote`): el ejecutable queda en una carpeta fuera del
PATH (ver [problemas conocidos](#8-problemas-conocidos-y-soluciones)).

**Reglas:** cerrar Thonny (un puerto no se comparte); conectar el rover por USB; para mover
motores hace falta además encender su batería de motores (el USB solo alimenta la lógica).

### Herramientas del repo (`herramientas/`)

| Herramienta | Qué hace | ¿Mueve algo? |
|---|---|---|
| `python herramientas/info_rover.py` | Lista los rovers conectados y muestra versión, UID y MAC | No (solo lectura) |
| `python herramientas/respaldar_rover.py COM3 rover1` | Copia los archivos propios del rover a `rover_original/rover1/` | No (solo lectura) |
| `python herramientas/probar_motores.py COM3 --ruedas-en-el-aire` | Gira cada motor 1.5 s al 40 %, uno por uno | **Sí: levantar el rover y encender baterías.** Se niega a correr sin el flag |
| `python herramientas/desplegar.py COM3` | Muestra qué archivos copiaría | No (simulación) |
| `python herramientas/desplegar.py COM3 --si` | Copia `comun/` + `firmware/` y **reemplaza `/code.py`** | Escribe en el rover (respaldar antes) |

### Comandos sueltos útiles

```bash
# Ejecutar código en el rover desde RAM (no guarda nada). Si falla con "could not enter raw repl",
# el rover está en un bucle: mandarle Ctrl-C primero (las herramientas del repo ya lo hacen).
python -m mpremote connect COM3 exec "import wifi; print(list(wifi.radio.mac_address))"

# Copiar un archivo hacia / desde el rover
python -m mpremote connect COM3 fs cp firmware/config.py :firmware/config.py
python -m mpremote connect COM3 fs cp :/code.py code_respaldo.py

# Consola en vivo (ver los print del firmware). Salir con Ctrl-]
python -m mpremote connect COM3 repl
```

### Lo que hizo Claude en esta sesión con los rovers

1. `mpremote connect list` → encontró `COM3` y `COM12` (chip CH340).
2. Identificó el firmware (`sys.implementation` → CircuitPython, no MicroPython).
3. Listó el sistema de archivos y **respaldó** los archivos propios en `rover_original/`
   (solo lectura).
4. Leyó la MAC de cada radio (`wifi.radio.mac_address`).
5. **Probó motores** uno por uno desde RAM (40 %, 1.5 s, con `try/finally` que frena siempre)
   con el rover levantado y la persona confirmando qué rueda giró.
6. **Probó ESP-NOW** desde RAM: un rover escucha 12 s y el otro manda 5 mensajes; luego al revés.
7. **No** subió nada al rover ni tocó sus `code.py`. El firmware todavía no está desplegado.

> CircuitPython **recarga solo** al guardar archivos en el rover y arranca `code.py` al
> encender/reiniciar. Al desplegar, el rover empieza a ejecutar el firmware apenas se
> reinicia: tener las ruedas en el aire y `VISION_HOST` configurado (si falta, el firmware
> aborta con un mensaje y deja los motores frenados).

### Sin cable USB: indicador LED

Para las pruebas en el suelo los rovers van **sin cable a la PC** (autonomía del reto, y el cable se
enreda). Sin USB no hay REPL ni `print`, así que el LED RGB de la placa dice qué hace el rover
(`firmware/indicador.py`):

| Color del LED | Significa |
|---|---|
| 🟡 Amarillo | Arrancando: conectando al WiFi / a la visión |
| 🔵 Azul tenue | Conectado a la visión, esperando que la ronda pase a `RUNNING` (no se mueve) |
| 🟣 Violeta | `BUSCAR` (sin cubo fresco que atender) |
| 🔵 Azul fuerte | `APROXIMAR` (yendo a ubicarse detrás del cubo) |
| 🟪 Magenta | `SUJETAR` (empujando hasta confirmar que lleva el cubo) |
| 🟢 Verde | `TRANSPORTAR` (empujando el cubo al depot) |
| 🩵 Cian | `ENTREGAR` (soltó el cubo, retrocede) |
| ⚪ Blanco | `OCIOSO` (terminó su cola de colores) |
| 🌸 Rosa | `DETENIDO` (ronda terminada, `FINISHED`) |
| 🟠 Naranja | Dejó de llegar telemetría: motores frenados |
| 🔴 Rojo | **Error** (p. ej. falta `VISION_HOST` en `settings.toml`): motores frenados. Conectar el USB y ver el mensaje con `mpremote ... repl` |

Antes de quitar el cable: confirmar que la placa **enciende con las baterías** (hoy no sabemos si la
batería de motores también alimenta la lógica), que `settings.toml` está copiado y que las ruedas
están en el aire para el primer arranque sin USB. El firmware arranca solo al dar energía y **no se
mueve** mientras la fase no sea `RUNNING`. La PC de visión debe seguir encendida y en la misma red.

---

## 5. Simulación y tests

```bash
pip install -r pc_dev/requirements.txt     # solo pytest
cd pc_dev
python -m pytest -q                        # 57 tests, ~2 s, sin hardware ni red
```

- `tests/test_ciclo_completo.py`: **lazo cerrado** — los 2 rovers entregan los 3 cubos (sin
  choques; también con ruido de visión de 0.15 y 0.3 celdas), no se mueven fuera de `RUNNING`,
  se detienen en `FINISHED`.
- `tests/test_firmware_main.py`: ejecuta `firmware/main.py` en la PC con módulos de hardware
  falsos (config por MAC, motores, paro seguro, exige `VISION_HOST`).
- `tests/test_navegacion.py`, `test_maquina_estados.py`, `test_mundo.py`: unidades.
- `python pc_dev/trazar_simulacion.py [ruido] [segundos]`: imprime los cambios de estado y choques
  de una corrida, útil para depurar la estrategia.

El simulador físico (`pc_dev/simulador_fisico.py`) es **propio** y simple (círculos que se empujan,
6 celdas/s y 90°/s a potencia máxima, escenario de `config_simulador.json` del repo guía). No
reemplaza al `mock_publisher.py` del repo guía: ese publica telemetría realista (ruido,
oclusiones) pero **no reacciona** a los comandos de los rovers.

---

## 6. Lo que falta por hacer

**Bloqueantes para la prueba real** (van en el plan de la sección 7):
- [ ] Configurar el WiFi de los rovers (`settings.toml`) y la IP de la PC de visión.
- [ ] Desplegar el firmware a los rovers y verlos conectarse y leer telemetría.
- [ ] Verificar la cámara y la cancha (marcadores, calibración).

**Calibración en banco/cancha (números hoy inventados por el simulador):**
- [ ] Velocidad lineal y de giro reales de cada rover vs. potencia (el simulador asume 6 celdas/s
  y 90°/s). Hay que calibrar la diferencia entre los dos motores (factores en `motores.py`) y
  la **potencia mínima** a la que las ruedas realmente arrancan.
- [ ] `DISTANCIA_AGARRE_CM` (hoy 4 cm, inventado) y dónde apunta el ultrasónico.
- [ ] **Rampa de aceleración** (limitar cuánto puede cambiar la potencia por ciclo) para arranques
  suaves; hoy solo existe `FACTOR_VELOCIDAD` (config.py).
- [ ] Constantes de `comun/planificador.py` (distancias de preagarre, rodeo, velocidades) y
  umbrales de `comun/maquina_estados.py`.
- [ ] Offset entre el centro del marcador ArUco y el centro real del chasis (el repo guía trae
  `vision/mediciones/desfases_rover10_*.json`).
- [ ] Geometría real de las paletas: el modelo asume que el cubo se empuja de frente.

**Sensores:**
- [ ] Integrar el sensor de color (I2C) para confirmar agarre/entrega; hoy solo hay ultrasónico.
- [ ] Confirmar el cableado del infrarrojo (conflicto de IO33 con el NeoPixel de prueba).
- [ ] Usar la IMU (giroscopio) para mantener rumbo entre cuadros de visión (20 Hz). El control
  actual es proporcional sobre el `theta` de la visión, sin PID.

**Lo complicado, dejado para el final a propósito:**
- [ ] **Negociación rover↔rover por ESP-NOW** (`comun/protocolo_rovers.py`, `firmware/comm_espnow.py`):
  hoy el reparto de colores es **estático por ID** (rover 10: rojo y azul; rover 11: verde) y
  el firmware ya puede enviar/recibir (probado) pero `main.py` **no lo usa todavía**.
  Falta: reclamar/liberar colores tolerando mensajes perdidos, reasignación dinámica (que un
  rover ayude al otro cuando termina), confirmar recolección/entrega.
- [ ] **Evitación de colisiones robusta.** Hoy: el rover de ID mayor cede el paso y se aparta, el
  de ID menor frena de emergencia; con ruido alto quedan roces ocasionales (≤2 por corrida en el
  simulador). Un campo de repulsión está implementado (`navegacion.repulsion`) pero apagado
  (`ganancia_repulsion=0`) porque empeoraba el empuje.
- [ ] Información imperfecta: hoy un cubo no fresco manda al rover a `BUSCAR` (quieto); falta un
  patrón de búsqueda y navegar hacia la última posición conocida.
- [ ] Botón de arranque de la IdeaBoard (hoy arranca solo al ver fase `RUNNING`).
- [ ] Obstáculos (el campo existe en el contrato pero la primera edición va vacío).

---

## 7. Plan paso a paso hasta la prueba real

Orden pensado para que **cada paso valide una sola cosa** y no se arriesgue el robot antes de
tiempo. No saltar pasos. Las ruedas en el aire son obligatorias hasta el paso 9.

### Tips para que funcione mejor (leer antes de empezar)

**1. Contar cuadros: la cancha es su propia regla.** 1 cuadro = 1 celda = 20 mm. Cada vez que
algo "parece raro", contar cuadros con los ojos es la comprobación más barata:

| Qué quieres saber | Cómo contar | Qué debe dar |
|---|---|---|
| ¿La cancha está bien montada? | Contar cuadros **de centro a centro** de dos marcadores de esquina vecinos | **43 cuadros** (860 mm). El tablero físico tiene 50×50 cuadros, pero el área de juego son 43×43: los 7 de diferencia son el margen donde van los marcadores. Si da otro número, el montaje está mal; no ajustar el código para compensar. |
| ¿La visión ubica bien? | Poner un cubo o rover en un cuadro conocido, contar desde el **centro del marcador 0** (origen) cuántos cuadros a la derecha (`col`) y hacia abajo (`row`), y comparar con lo que reporta `test_client.py` o la ventana | Coincidir con ≤ 1 cuadro de diferencia. Si `col` no sube al ir a la derecha o `row` no sube al ir hacia abajo, los marcadores están en orden equivocado. |
| ¿Qué tan rápido va el rover? | Marcar un cuadro de salida, avanzar con potencia fija un tiempo medido (cronómetro) y **contar cuadros recorridos**; velocidad = cuadros ÷ segundos. Repetir 3 veces y promediar | Anotar el valor por rover y por potencia; compararlo con lo que asume el simulador (6 celdas/s a potencia 1.0, `VEL_MAX` en `pc_dev/simulador_fisico.py`). |
| ¿Se desvía al ir "recto"? | Avanzar 20 cuadros y contar cuántos cuadros **de lado** se corrió | Desvío ≈ 0. Si siempre se corre al mismo lado, ajustar los factores de calibración izquierda/derecha de `firmware/motores.py`. |
| ¿Cuánto gira? | Girar en el sitio un tiempo fijo y leer `theta` en la vista de la cámara antes y después | Grados por segundo por rover (el simulador asume 90°/s a potencia 1.0, `GIRO_MAX`). |
| ¿A qué distancia "ve" el cubo el ultrasónico? | Poner el cubo a 1, 2, 3… cuadros del frente y leer el sensor (un cubo mide 3 cuadros de lado) | Fija `DISTANCIA_AGARRE_CM` en `firmware/config.py`. |

Anotar los resultados (rover, potencia, cuadros, segundos) en un archivo del repo, p. ej.
`docs/calibracion.md`, para no repetir mediciones.

**2. Movimientos muy suaves primero, optimizar después.**

- **Orden de pruebas, de menos a más riesgo:** ruedas en el aire → suelo, espacio libre, sin cubos →
  un cubo con un solo rover → los dos rovers. No pasar al siguiente hasta repetir 3 veces el actual sin
  fallos.
- **`FACTOR_VELOCIDAD` en `firmware/config.py`** (hoy **0.5**) multiplica las velocidades de avance y de
  empuje del planificador. Empezar con 0.5 (o menos) y subirlo de 0.1 en 0.1 **solo** después de 3
  corridas limpias. Si a un valor bajo las ruedas ni arrancan, el motor tiene una **potencia mínima**:
  subirlo hasta que arranque y anotar ese valor.
- **Cambiar una sola cosa por prueba** y anotar qué se cambió; si no, no se sabe qué arregló o rompió.
- **Lo que el factor NO suaviza** (se edita a mano si hace falta aún más suavidad): los giros en el
  sitio (`w_max` y el piso de giro en `comun/navegacion.py: comando_hacia_rumbo`) y la marcha atrás
  (`VEL_RETROCESO` en `comun/planificador.py`). Tampoco hay **rampa de aceleración** todavía (los
  arranques son bruscos): está en la lista de pendientes.
- **Siempre una forma de cortar**: mano junto al interruptor de la batería de motores; `f` (stop) en la
  vista de la cámara; `Ctrl-C` en el REPL del rover. El firmware frena los motores solo si se pierde la
  telemetría por más de 0.5 s.
- **Empuje suave = el cubo no se escapa.** En el simulador el caso que más falla es el cubo que se
  resbala hacia un lado al empujarlo demasiado rápido.
- **Después de que funcione a baja velocidad** se optimiza: subir `FACTOR_VELOCIDAD` hacia 1.0, reducir
  distancias de preagarre/rodeo en `comun/planificador.py`, recalibrar los números del simulador con lo
  medido y volver a correr `pytest`.

### Fase A — Sistema de visión y cámara (solo PC, sin rovers)

Guías completas en el repo guía: `vision-system/MONTAJE.md`, `PUESTA_A_PUNTO.md`, `OPERACION.md`.

**Progreso (30-sep-2026):** pasos 1, 2 y 3 **hechos y verificados** en esta PC. El sistema de visión
está en `C:/Users/Allis/Documents/guia/vision-system` (con su `.venv`); `verificar_geometria` da
`TODO OK`; el mock + `test_client` intercambiaron 80 mensajes sin pérdidas; y nuestro
`ejecutar_simulacion.py` leyó el mock real (el rover se queda quieto en `READY`, como debe).
**Paso 5 (elegir cámara) hecho:** la webcam **Logitech C270** está conectada. Ojo: `--listar` dice
`[0] Logi C270` y `[1] Integrated Camera`, pero **la que mira el tablero es el índice 1** (`--indice 1`; el
índice 0 sale negro). El nombre no coincide con el número, tal como advierte el repo guía: se confirma
**mirando la imagen**. Con `--indice 1 --camara logitech_c270` el sistema abre la C270 a 1280x720, el
perfil sale *compatible* y publica en el puerto 2026.

```bash
cd C:/Users/Allis/Documents/guia/vision-system
set PYTHONIOENCODING=utf-8        # en cmd; en PowerShell: $env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python -m vision.sistema --indice 1 --camara logitech_c270 --ventana
```

**Primer hallazgo con la cámara real:** en la primera imagen solo se veía completo **1 de los 4
marcadores de esquina** (el ID 2); los otros estaban cortados por el borde o fuera de cuadro, y el
sistema no publicó coordenadas (rovers y cubos vacíos). Se reubicó la cámara hasta ver los 4 (ver abajo).

**✅ Pasos 4, 5, 7 y 8 hechos y verificados con la cámara real (30-sep-2026):**

| Comprobación | Resultado |
|---|---|
| Los 4 marcadores de esquina | Detectados (`Esquinas 4 de 4`), en **orden horario**: 0 arriba-izquierda, 1 arriba-derecha, 2 abajo-derecha, 3 abajo-izquierda |
| Zonas y salida | Verde arriba, roja a la derecha, azul abajo, salida al centro del lado izquierdo (donde la organización las espera) |
| Coordenadas | Contando celdas desde el marcador 0 a mano, el cubo rojo dio col ≈ 20, igual que la visión |
| Sentido de los ejes | Al mover un cubo a la izquierda y hacia abajo: `col` bajó (34.3 → 23.3) y `row` subió (24.2 → 39.6) ✔ |
| Veredicto de entrega | Cubo azul en (23.30, 39.57) → la visión lo marcó **EN POSICIÓN**; coincide con `mundo.cubo_en_su_zona` (banda col 18.6–24.4, row 37.6–40.9) |
| Oclusión | Un cubo tapado (sombra/mano) se quedó con `edad 10100 ms` en naranja: la visión conserva la última posición. Nuestro código lo trata como poco confiable |
| Rovers 10 y 11 | Ambos detectados, con el marcador hacia arriba y el frente a la derecha: **`theta` 358.4° y 358.7°** (posiciones (4.08, 17.39) y (4.25, 24.76), casi iguales a las de salida del simulador). El frente real del robot **coincide** con el "adelante" del marcador |
| Sentido del giro | Girados a mirar hacia arriba del tablero: **`theta` 86.9° y 89.4°** → `theta` **sube en sentido antihorario**, como espera `comun/navegacion.py` |

Notas de esta prueba:
- El sistema procesa a **~10 cuadros por segundo** a 1280x720 (publica a 20 Hz, pero el dato se refresca a 10). El
  control actual lo tolera; tenerlo en cuenta al calibrar velocidades.
- Un rover recién puesto tarda ~0.5 s en aparecer (la visión exige 5 cuadros estables) y aparecieron
  detecciones falsas momentáneas de "rover 10" sobre la cuadrícula con la cancha vacía; se descartan solas.
- **Solo un programa puede usar la cámara a la vez**: hay que cerrar el sistema de visión (`q` en la ventana)
  antes de correr `diagnostico_camara`, la calibración o la medición de precisión.
- Se usó el **perfil de cámara que ya trae el repo** (`logitech_c270`), aceptado como *compatible*. La
  **calibración propia** (paso 6, `PUESTA_A_PUNTO.md`) está pendiente; ver la guía abajo.

**Qué hay que conseguir / conectar para los pasos 4 a 8** (nada de esto es para conectar los rovers):

| Qué | Para qué | Estado |
|---|---|---|
| **Webcam USB externa** (el repo trae perfiles para *Logitech C270* y *Argomtech CAM40*) | La cámara cenital | ✅ **Detectada** (Logi C270, `--indice 1`). Falta el soporte/altura para que vea los 4 marcadores. |
| **Soporte para la cámara, mirando la cancha desde arriba** | Que vea los 4 marcadores de esquina completos. El repo trae una base para techo en `archivos_fabricacion/WebCam Base.stl` (impresión 3D, 4 tornillos con tuerca de 3/16" y 1 de 1/4", de 2 cm); un trípode o soporte improvisado sirve para probar. | Por definir |
| **La cancha**: superficie de 1 m × 1 m cuadriculada (celdas de 2 cm) | Donde se mueven los rovers. Archivos: `archivos_fabricacion/cuadricula_1m_2cm_bn.svg` y `Cuadricula 1mx1m ArUco.pdf` | ¿Ya está impresa/armada? |
| **4 marcadores de esquina** (IDs 0, 1, 2, 3, de 10 cm, con margen blanco) | Definen el sistema de coordenadas | Imprimir de `aruco/aruco_id0..3_negro10cm.pdf` **al 100 % de escala** y medir con regla |
| **Cubos de 6 cm** rojo, verde y azul | Los objetos del reto (`archivos_fabricacion/cubos.dxf`) | ¿Ya están? |
| Impresora, regla/cinta con mm, cartón o tabla rígida, cinta adhesiva | Calibración de la cámara (`PUESTA_A_PUNTO.md`) y pegar marcadores | — |
| Los 2 rovers con sus stickers 10 y 11 | Paso 8 (verlos en la ventana). **Sin motores ni baterías**, solo ponerlos en la cancha | Stickers ya pegados |

> En los pasos 4 a 8 los rovers **no necesitan estar conectados por USB ni encendidos**: solo se usan
> como objetos con un marcador.

1. ✅ **Clonar e instalar el sistema de visión** (Python ≥ 3.10) — *hecho*:
   ```bash
   git clone https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge.git ../Vision-Rover-Challenge
   cd ../Vision-Rover-Challenge/vision-system
   python -m venv .venv
   .venv\Scripts\python -m pip install -r vision/requirements.txt      # Windows
   ```
2. ✅ **Comprobar la instalación** (no usa la cámara) — *hecho*. Debe terminar en `RESULTADO GENERAL: TODO OK`:
   ```bash
   .venv\Scripts\python -m vision.tools.verificar_geometria
   ```
3. ✅ **Probar el contrato sin cámara** — *hecho*: `python contrato/mock_publisher.py` en una terminal y
   `python contrato/test_client.py` en otra (no requiere el venv). El mock **lee comandos por teclado y se
   cierra si no tiene entrada** (p. ej. lanzado en segundo plano sin stdin): déjalo en una terminal
   interactiva. Con `ready` pasa a `READY` y tras 60 s a `RUNNING`.
4. **Montar la cancha** (`MONTAJE.md`): los 4 marcadores de esquina (IDs 0–3) pegados con su margen
   blanco; los rovers con sus stickers (**10 y 11**, ya puestos); los cubos rojo/verde/azul.
5. **Elegir la cámara**: `.venv\Scripts\python -m vision.tools.diagnostico_camara --listar` y luego
   sin `--listar` para **mirar la imagen** (el índice no coincide con el orden del nombre). Anotar el
   índice; si no es 0, usar `--indice N` en los comandos siguientes.
6. **Calibrar la cámara** (`PUESTA_A_PUNTO.md`, necesita imprimir el patrón, regla y cartón). Si el
   repo ya trae un perfil para tu modelo (`vision/calibraciones/logitech_c270.json`,
   `argomtech_cam40.json`), se puede usar ese.
7. **Vista en vivo**: `.venv\Scripts\python -m vision.sistema --ventana` y comprobar mirando
   (`MONTAJE.md` §6): los 4 marcadores detectados; el origen en el marcador 0; `col` aumenta hacia la
   derecha y `row` hacia abajo (si no, los marcadores están en orden antihorario); la grilla
   dibujada cae sobre la cuadrícula; las zonas (verde arriba, roja derecha, azul abajo) y la salida
   (centro del lado izquierdo) están donde la organización espera.
8. **Ver que los rovers se detectan**: poner un rover en la cancha y confirmar en la ventana los IDs
   10 y 11 con su flecha de orientación. Mover uno hacia la derecha y comprobar que `col` sube;
   girarlo antihorario y comprobar que `theta` sube. Con `python contrato/test_client.py` se ve el
   mensaje v2 real.

#### Paso 6 en detalle: calibrar la cámara (`PUESTA_A_PUNTO.md` del repo guía)

Todo lente curva las líneas rectas y eso corre las posiciones que calcula la visión. Se mide cuánto
curva **nuestra** cámara y se guarda como un perfil propio. Lo que sigue es lo que hay que hacer; el
detalle y las explicaciones están en `vision-system/PUESTA_A_PUNTO.md`.

> **Regla: el repo guía no se modifica.** La herramienta guarda el perfil en
> `vision-system/vision/calibraciones/<nombre>.json`. Para no pisar el `logitech_c270.json` que trae el
> repo, **usar un nombre propio**, p. ej. `"NullPointer C270"`, que crea un archivo nuevo (sin versionar) y
> no toca ninguno existente. Después, copiar ese JSON a una carpeta de este repo como respaldo.

Materiales: impresora, regla con mm, cartón/cartulina gruesa o tabla lisa, pegamento (en **toda** la
superficie), tijeras. Los PDF ya están generados en [`calibracion/`](calibracion/):
`patron.pdf` (3 páginas: 2 del ajedrezado + instrucciones) y `marcador_prueba.pdf` (ID 20, 60 mm).

1. **Imprimir al 100 % de escala** (nunca "ajustar a la página") y **medir con la regla la línea de 100 mm**
   que trae cada hoja al pie. Si no mide 100 mm, reimprimir: no seguir.
2. **Armar el patrón**: cortar una hoja por la línea gris, pegar las dos **a tope** (sin escalón ni hueco) y
   pegar todo sobre cartón rígido, **plano** (cada ondulación se toma como distorsión del lente). Recortar el
   marcador de prueba **dejando su borde blanco** y pegarlo también plano.
3. **Cerrar el sistema de visión** (tecla `q` en su ventana): la cámara solo la puede usar un programa a la vez.
4. **Calibrar** (desde `C:/Users/Allis/Documents/guia/vision-system`, con `PYTHONIOENCODING=utf-8`):
   ```bash
   .venv\Scripts\python -m vision.tools.calibrar_camara --indice 1 --camara "NullPointer C270"
   ```
   Mostrar el patrón en posiciones **variadas**: las 9 zonas del cuadro (sobre todo las esquinas), 3
   distancias y al menos 4 vistas inclinadas. Seguir la línea `>` del panel, no el contador de capturas;
   cuando diga "ya alcanza", apretar `C`. Esperar el veredicto: **EXCELENTE/BUENA** sirven; **MALA** no
   guarda el perfil (casi siempre es que el patrón no estaba plano).
5. **Verificar a ojo**: `... calibrar_camara --verificar --indice 1 --camara "NullPointer C270"` muestra la imagen
   original y la corregida con una rejilla recta; las líneas del tablero deben quedar rectas a la derecha.
6. **Medir la precisión**: `... precision_ubicacion --camara "NullPointer C270"` (usa el marcador de prueba
   sobre el tablero, alineado a la cuadrícula). Contar cuadros da la distancia real (ver los tips). Anotar el
   error en mm en `docs/calibracion.md`.
7. **Usar el perfil nuevo**: lanzar la visión con `--camara "NullPointer C270"` en vez de `logitech_c270` y
   repetir la comprobación de los rovers (pasos 7 y 8): las posiciones y los `theta` deben seguir igual o
   mejorar.

### Fase B — Rover con ruedas en el aire, telemetría simulada

9. **Red**: la PC y los rovers deben estar en la **misma red WiFi de 2.4 GHz** (el ESP32 no usa 5 GHz).
   Averiguar la IP de la PC (`ipconfig`) y **permitir el puerto 2026** en el firewall de Windows.
   Levantar el `mock_publisher.py` (escucha en `0.0.0.0:2026`).
10. **Probar el controlador en la PC contra el mock** (sin rover):
    ```bash
    python pc_dev/ejecutar_simulacion.py --host 127.0.0.1 --port 2026 --id 10
    ```
    Debe mostrar estados y ruedas `(izq, der)`. (El mock no reacciona a las ruedas: es solo para ver
    la decisión.)
11. **`settings.toml` en cada rover** (copiar `firmware/settings.toml.example` y completar con el WiFi
    real y `VISION_HOST` = IP de la PC). Se copia con
    `python -m mpremote connect COM3 fs cp settings.toml :settings.toml`. **No subirlo al repo**
    (está en `.gitignore`).
12. **Respaldar y desplegar** el rover 1 (un rover primero):
    ```bash
    python herramientas/respaldar_rover.py COM3 rover1      # ya hecho, repetir si hay dudas
    python herramientas/desplegar.py COM3                    # revisar la lista
    python herramientas/desplegar.py COM3 --si
    ```
13. **Ver el arranque**: con el rover **levantado (ruedas en el aire)**, reiniciarlo y abrir
    `python -m mpremote connect COM3 repl`. Debe imprimir `rover 10 conectando WiFi...` y
    `conectado a vision <IP> 2026`, y después, al cambiar la fase, los estados
    (`READY`/`RUNNING` + estado). Si aborta, el mensaje dice por qué (p. ej. falta `VISION_HOST`).
14. **Con la cámara real, rover levantado**: en la ventana de visión dar `r` (ready); tras la
    preparación (1 min por defecto, configurable en `vision/config_vision.json`, bloque `ronda`) pasa a
    `RUNNING` solo. Verificar que las ruedas reaccionan coherentemente: poner un cubo, y ver que el
    rover intenta girar hacia donde está (mover el rover a mano no cambia nada; el objetivo es ver el
    sentido de giro). Comprobar que `f` (stop) o `FINISHED` **frena** las ruedas.
15. **Repetir 12–14 con el rover 2** (`COM12`).

### Fase C — Calibración con los rovers

16. **Potencia mínima y velocidad** (contando cuadros, ver los tips de arriba): con el rover en el suelo y un espacio libre, medir cuánta potencia
    hace falta para arrancar y cuánto avanza por segundo a 0.5, 0.7 y 1.0; y cuánto gira por segundo
    en el sitio. Ajustar `_factor_izq/_factor_der` en `motores.py` hasta que avance recto y actualizar
    las constantes del simulador (`VEL_MAX`, `GIRO_MAX`) con lo medido.
17. **Offset del marcador**: comparar la posición que reporta la visión con la del chasis
    (`vision/mediciones/desfases_*.json`).
18. **Agarre**: con un cubo delante, leer el ultrasónico (`python -m mpremote connect COM3 exec ...`
    con `hcsr04`) a distintas distancias y fijar `DISTANCIA_AGARRE_CM`.

### Fase D — Prueba real en cancha (escalonada)

19. **Un rover, un cubo, sin el otro** (el otro apagado o fuera). Cubo cerca y depot cercano.
    Cronómetro y mano sobre el botón de apagado. Esperado: aproxima, empuja, entrega, retrocede.
    Anotar qué falla (agarre, giro, cubo que se escapa) y ajustar constantes en `planificador.py`.
    Reproducir el fallo en `simulador_fisico.py` si es posible, arreglar, correr `pytest`, redesplegar.
20. **Un rover, su cola completa** (rover 1: rojo y azul).
21. **Los dos rovers, cada uno con su color**, cubos lejos entre sí (sin cruces).
22. **Escenario completo** (config del repo guía: 3 cubos, salida a la izquierda) y medir el tiempo con
    el cronómetro oficial de la visión (`vision/actas/` guarda un acta por ronda).

### Fase E — Lo complicado

23. Negociación por ESP-NOW y reasignación dinámica; evitación de colisiones robusta; búsqueda de
    cubos ocluidos; usar la IMU. Cada uno con tests en el simulador **antes** de ir al robot.

---

## 8. Problemas conocidos y soluciones

| Síntoma | Causa y solución |
|---|---|
| `python` abre la Microsoft Store o "no está instalado" | Alias de ejecución de la Store intercepta `python.exe`. Desactivar los alias de `python.exe`/`python3.exe` en Configuración → Aplicaciones → Alias de ejecución, o llamar al intérprete real por ruta completa. |
| `pip install mpremote` falla con `WinError 2 ... pyserial-miniterm.exe.deleteme` | Sin permisos en `C:\Python312\Scripts`. Usar `pip install --user mpremote` y ejecutarlo como `python -m mpremote`. |
| `mpremote` → `could not enter raw repl` | El rover está corriendo un `code.py` con bucle infinito. Mandar Ctrl-C por serial (las herramientas del repo lo hacen solas). |
| `mpremote` no ve el puerto / "access denied" | Thonny u otro programa tiene el puerto abierto. Cerrarlo. |
| `git clone` falla con `Filename too long` | Clonar en una ruta corta, p. ej. `C:\Users\<usuario>\Documents\Null-Pointer`. |
| `fs ls` de mpremote da error `ilistdir` | CircuitPython no lo soporta; listar con `os.listdir` vía `exec` (lo hace `respaldar_rover.py`). |
| En el ESP-NOW de CircuitPython, `e.send(...)` devuelve falsy aunque el mensaje llegó | Es normal: el valor no indica éxito. Verificar del lado receptor. |
| El `mock_publisher.py` se cierra solo / `test_client` da `WinError 10061` | El mock lee comandos por stdin y termina si no hay entrada. Correrlo en una terminal normal (no en segundo plano) y esperar ~3 s antes de conectar el cliente. |
| `vision.sistema` se cae con `UnicodeEncodeError ... '✓'` | Windows usa una codificación que no tiene el símbolo ✓ (pasa sobre todo al redirigir la salida). Definir `PYTHONIOENCODING=utf-8` antes de lanzarlo. |
| `IdeaBoard` falla con "pin in use" | Se creó la placa dos veces. Todo el firmware la pide por `firmware/placa.py` (una sola instancia); no hacer `IdeaBoard()` en otros módulos. |
| `diagnostico_camara --listar` solo muestra `Integrated Camera` | La webcam USB externa no está conectada, o Windows no le dio permiso de cámara. Conectarla y repetir. |
| El firmware aborta con `Falta VISION_HOST` | Falta `VISION_HOST` en el `settings.toml` del rover. |
| `RuntimeError: MAC desconocida` al arrancar | Una placa distinta a las dos registradas: agregar su MAC a `ROVERS` en `firmware/config.py`. |
| El rover no conecta al WiFi | Red de 5 GHz (usar 2.4), SSID/clave mal escritos en `settings.toml`, o PC en otra red. |
| El rover conecta pero no recibe telemetría | Firewall de Windows bloqueando el puerto 2026 en la PC de visión, o IP equivocada. |

---

## 9. Flujo de trabajo con git

- `main`: vacía a propósito por ahora (solo el commit inicial). **No hay PR a `main` todavía** —
  se hará cuando el equipo decida una versión estable.
- `develop`: rama de integración; todo entra por PR (PRs #1–#5 ya fusionados).
- Ramas de trabajo: `feat/...`, `fix/...`, `chore/...`, siempre contra `develop`.
- Commits con `Co-Authored-By` cuando los escribe Claude Code.
- El `settings.toml` de los rovers (WiFi) está en `.gitignore`: **no subirlo**.

---

## 10. Referencias

- Repo guía del reto (reglas, specs, sistema de visión): [Vision-Rover-Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge)
  — `el_reto.md`, `robot.md`, `reglamento.md`, `vision-system/contrato/CONTRATO.md`, `codigos/` (ejemplos de
  PID, IMU, color, ESP-NOW que aún no adaptamos).
- Protocolo de telemetría (resumen propio): [`docs/contrato_telemetria.md`](docs/contrato_telemetria.md)
- Arquitectura y decisiones: [`docs/arquitectura.md`](docs/arquitectura.md)
- Firmware y despliegue: [`firmware/README.md`](firmware/README.md)
- Simulación: [`simulacion/README.md`](simulacion/README.md)
