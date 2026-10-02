# Null-Pointer — Vision Rover Challenge

> **Actualización local, 1-oct-2026:** firmware compartido con líder por MAC de
> 48 bits, ESP-NOW integrado y reparto por distancia. Rover 1 en COM3 y rover 2
> en COM4. **71 pruebas pasan**, incluida entrega de los tres cubos con pérdidas
> de radio simuladas. Desplegado en COM3 y COM4: 19 archivos verificados byte a
> byte por placa e importación correcta. Pendiente probar movimiento y radio
> con el programa completo en cancha. Detalles y
> límites en [coordinación ESP-NOW](docs/coordinacion_espnow.md).
> Las tablas y el plan del 30-sep que siguen documentan el estado anterior.

Proyecto del equipo para el [Vision Rover Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge)
de Cenfotec: dos CenfoBot (IdeaBoard ESP32, **CircuitPython**) deben ubicar, transportar y depositar cubos de
color en su zona, coordinándose entre sí. Un sistema de visión externo (cámara cenital) **solo da percepción**
(posición y orientación); **toda la decisión corre a bordo de los rovers**, sin PC externa durante la ronda.

> **Última actualización:** 30-sep-2026 · rama `develop` · 63 tests en verde · 13 PRs fusionados.
> `main` está vacía a propósito (no hay PR a `main` todavía).

---

## Estado de un vistazo

✅ comprobado en hardware real · 🧪 comprobado solo en simulación/tests · ⚠️ hecho pero con algo sin comprobar ·
⏳ pendiente · ⏭️ omitido a propósito

| Área | Estado | En una línea |
|---|---|---|
| Cámara + sistema de visión (repo guía) | ✅ | Logitech C270, 4 marcadores en orden horario, zonas y ejes correctos |
| Detección de los rovers 10 y 11 | ✅ | Posición y `theta` correctos (0° a la derecha, sube al girar antihorario) |
| Conexión USB a los rovers (`mpremote`) | ✅ | Leer, respaldar, ejecutar, desplegar |
| Motores: cuál es izquierda/derecha | ✅ | `motor_1` = izquierda, `motor_2` = derecha, sin invertir (ambos rovers) |
| ESP-NOW entre los dos rovers | ✅ | 5/5 mensajes en ambos sentidos · ⏳ el firmware aún no lo usa |
| WiFi + telemetría real en los rovers | ✅ | Red `Visitas` (2.4 GHz); ambos se conectaron a la visión |
| Lógica de decisión (`comun/`) | 🧪 | 2 rovers entregan los 3 cubos en ~30 s simulados, 0 choques |
| Firmware en el rover 1 | ⚠️ | Desplegado y conectado; **ningún movimiento de ruedas probado** |
| Firmware en el rover 2 | ⚠️ | **Despliegue interrumpido** (cable USB): hay que repetirlo |
| LED de estado | ⚠️ | Pin IO33 confirmado en rover 1; paleta nueva sin ver; rover 2 sin confirmar |
| Movimiento con el firmware completo | ⏳ | Primera prueba (ruedas en el aire) es el siguiente paso |
| Sensor de agarre (ultrasónico) | ⏳ | Sin probar ni calibrar (`DISTANCIA_AGARRE_CM` es un número inventado) |
| Sensor de color / IMU | ⏳ | Sin integrar |
| Coordinación entre rovers por ESP-NOW | ⏳ | Hoy el reparto de colores es fijo (rover 10: rojo y azul; rover 11: verde) |
| Evitación de colisiones robusta | ⏳ | Hoy solo una regla simple de ceder el paso |
| Calibración propia de la cámara | ⏭️ | Se espera que la cámara del reto ya venga calibrada |

**Siguiente paso inmediato:** reconectar los rovers → repetir el despliegue del rover 2 → confirmar el LED →
primera prueba de movimiento con las ruedas en el aire. Detalle en el [plan](#9-plan-completo-lo-que-falta-paso-a-paso).

---

## Para quien retoma el proyecto: qué NO está en el repo y qué hay que preparar

Si clonas el repo en otra PC (o mañana en la misma), **hay cosas que Git ignora a propósito** y que no vienen en el
`git clone`. Sin ellas el firmware no conecta o la visión no corre:

| Qué NO viene en el repo | Por qué | Qué hay que hacer |
|---|---|---|
| `firmware/settings.toml` | Tiene la **contraseña del WiFi** | Crearlo copiando `firmware/settings.toml.example`: red `Visitas`, la contraseña (pedirla al equipo) y `VISION_HOST` = IP de **la PC que corre la visión** (`ipconfig`). **Nunca** escribirlo en el `.example` |
| El `settings.toml` que **ya está dentro de cada rover** | Vive en el flash del rover, no en el repo | Hoy tiene la IP `192.168.51.119` (la PC de esta sesión). **Si la visión corre en otra PC, o la PC cambia de red/IP, hay que actualizarlo en los dos rovers** (si no, conectan al WiFi pero no ven la visión) |
| El **sistema de visión** (repo guía) | Es de otra organización y **no se modifica** | Clonarlo aparte y crear su `.venv` (ver [§11](#11-guía-de-la-cámara-y-el-sistema-de-visión)). Las rutas de este README (`C:/Users/Allis/...`) son las de esta PC: ajustarlas |
| El **índice de la cámara** (`--indice`) | Depende de la PC (aquí la C270 es el 1) | `diagnostico_camara --listar` y **mirar la imagen**; no fiarse de los nombres |
| `mpremote` y `pytest` | Son herramientas, no código | `pip install --user mpremote` · `pip install -r pc_dev/requirements.txt` |
| Los **puertos COM** de los rovers | Cambian al reconectar | `python herramientas/info_rover.py` y reconocer cada rover por su UID/MAC |
| `fotos/`, `.venv`, `__pycache__` | Capturas y archivos locales | No hacen falta |

**Checklist para retomar (en orden):**

1. `git clone` en una ruta corta, `git checkout develop`, instalar `pytest` y correr `cd pc_dev && python -m pytest -q`
   → deben pasar **63 tests**.
2. Poner la PC en la **misma red de 2.4 GHz que los rovers** (`Visitas`) y anotar su IP (`ipconfig`).
3. Instalar y levantar el sistema de visión (§11) y comprobar que ve los **4 marcadores** y los rovers.
4. Crear `firmware/settings.toml` con esa IP.
5. Conectar los rovers por USB (cerrar Thonny) y correr `info_rover.py`.
6. **Pendiente conocido:** repetir el despliegue del **rover 2** (quedó a medias) y, si la IP cambió, volver a copiar el
   `settings.toml` a los dos rovers.
7. `probar_led.py` en ambos y, **con las ruedas en el aire**, la primera prueba de movimiento (Fase C del plan, §9).

---

## Índice

1. [Cómo está organizado el proyecto](#1-cómo-está-organizado-el-proyecto)
2. [Lo que se hizo](#2-lo-que-se-hizo)
3. [Qué funciona y cómo se comprobó](#3-qué-funciona-y-cómo-se-comprobó)
4. [Los rovers: hardware y datos medidos](#4-los-rovers-hardware-y-datos-medidos)
5. [Cómo nos conectamos a los rovers](#5-cómo-nos-conectamos-a-los-rovers)
6. [Indicador LED (para probar sin cable)](#6-indicador-led-para-probar-sin-cable)
7. [Cómo correr cada cosa](#7-cómo-correr-cada-cosa)
8. [Lo que falta: por comprobar, calibrar y construir](#8-lo-que-falta-por-comprobar-calibrar-y-construir)
9. [Plan completo: lo que falta, paso a paso](#9-plan-completo-lo-que-falta-paso-a-paso)
10. [Tips para que funcione mejor](#10-tips-para-que-funcione-mejor)
11. [Guía de la cámara y el sistema de visión](#11-guía-de-la-cámara-y-el-sistema-de-visión)
12. [Problemas conocidos y soluciones](#12-problemas-conocidos-y-soluciones)
13. [Flujo de trabajo con git](#13-flujo-de-trabajo-con-git)
14. [Referencias](#14-referencias)

---

## 1. Cómo está organizado el proyecto

```
  Cámara cenital ──► Sistema de visión (PC, repo guía, NO se modifica)
                              │  WiFi · TCP puerto 2026 · NDJSON · ~20 Hz (la cámara procesa a ~10)
                  ┌───────────┴───────────┐
                  ▼                       ▼
              Rover 10  ◄── ESP-NOW ──►  Rover 11        (cada rover decide solo: comun/ + firmware/)
```

| Carpeta | Dónde corre | Qué contiene |
|---|---|---|
| [`comun/`](comun/) | **PC y rover** (mismo código) | **Toda la decisión.** `contrato.py` (constantes), `mundo.py` (emparejar por identidad, frescura, latencia), `maquina_estados.py` (FSM), `navegacion.py` (geometría y control de rumbo), `planificador.py` (a dónde ir según el estado), `rover.py` (`ControladorRover`: FSM + planificador + reparto de colores + ceder el paso), `protocolo_rovers.py` (mensajes entre rovers y reparto estático). |
| [`firmware/`](firmware/) | Solo rover (CircuitPython) | Lo que toca hardware: `motores.py`, `sensores.py`, `indicador.py` (LED), `placa.py` (una sola `IdeaBoard`), `comm_vision.py` (TCP), `comm_espnow.py`, `config.py` (identidad por MAC), `main.py` (loop), `code.py` (arranque), `settings.toml.example`. |
| [`pc_dev/`](pc_dev/) | Solo PC | `simulador_fisico.py` (lazo cerrado), `ejecutar_simulacion.py`, `trazar_simulacion.py`, `tests/` (pytest). |
| [`herramientas/`](herramientas/) | PC, habla con los rovers por USB | `info_rover.py`, `respaldar_rover.py`, `probar_motores.py`, `probar_led.py`, `desplegar.py`. |
| [`rover_original/`](rover_original/) | — | Respaldo del contenido de fábrica de cada rover (`rover1/`, `rover2/`), para restaurarlos. |
| [`calibracion/`](calibracion/) | — | PDF del patrón de calibración de cámara (generados, **no hace falta imprimirlos** por ahora). |
| [`docs/`](docs/) | — | [`contrato_telemetria.md`](docs/contrato_telemetria.md) (protocolo v2) y [`arquitectura.md`](docs/arquitectura.md). |
| [`simulacion/`](simulacion/) | — | Cómo usar el `mock_publisher` del repo guía. |

**Idea central:** la lógica (`comun/`) se escribe una sola vez, se prueba con `pytest` en la PC y se copia
**sin cambios** al rover. Lo que funciona en simulación es lo que corre en el robot.

**Estrategia del rover:** el cubo se **empuja** con el frente (entre las paletas). El rover se ubica **detrás del
cubo** (lado opuesto al depot), avanza siguiendo la línea cubo→depot corrigiendo el desvío lateral, suelta cuando la
visión confirma el cubo dentro de la zona (con 1 celda de margen), retrocede y pasa a su siguiente color. Si el cubo
se escapa, lo recupera. No se mueve fuera de la fase `RUNNING` y se detiene en `FINISHED`.

### Cómo arranca el código en el rover (y por qué existe el repositorio)

**Pregunta frecuente:** *"CircuitPython solo corre un archivo llamado `code.py`; ¿por qué tenemos tantos archivos y un
repositorio?"*

- **Es cierto:** al encender, CircuitPython solo ejecuta por sí mismo un archivo en la **raíz** del rover llamado
  `code.py` (o `main.py`). Ningún otro archivo corre solo.
- **Nuestro `code.py` es un lanzador de dos líneas** (`firmware/code.py`): llama a `firmware/main.py`, y este importa
  `comun/`, los motores, los sensores y el LED. Es un programa normal de varios archivos, con `code.py` como puerta de entrada.
- **El código SÍ está en los robots.** `desplegar.py` copia los 18 archivos (`comun/`, `firmware/` y el `code.py`) al
  rover, y se comprobó: al reiniciar imprimió `conectado a vision 192.168.51.119 2026` y la visión lo listó como cliente.
  (Estado actual: rover 1 desplegado; rover 2 con el despliegue a medias, ver la [tabla de estado](#estado-de-un-vistazo).)
- **Para qué sirve el repositorio, si el código ya está en los robots:**
  1. **Fuente única y respaldo:** si el flash de un rover se daña o se sobrescribe, el código sigue en GitHub; los rovers
     solo reciben una copia.
  2. **Trabajo en equipo e historial:** quién cambió qué, revisión por PR, poder volver atrás. Dentro del robot no hay nada de eso.
  3. **Probar sin los robots:** `comun/` corre en la PC con 63 tests y un simulador, y así se encuentran errores antes de
     arriesgar el hardware (ya se encontraron fallos reales de esa forma).
  4. **Dos robots, un solo código:** cada rover se identifica por su MAC; desplegar es copiar los mismos archivos a ambos.

---

## 2. Lo que se hizo

Todo está en `develop`, entrado por PR:

| PR | Qué | Resultado |
|---|---|---|
| #1 | Esqueleto inicial: `comun/`, `firmware/`, `pc_dev/`, docs | 24 tests |
| #2 | Protocolo de telemetría **v2** (`clock`, `depot_size`, `cube_side`, zonas rectangulares) | Entrega verificada con la fórmula exacta del contrato |
| #3 | Migración a **CircuitPython** (los rovers no usan MicroPython) | `firmware/` reescrito con `ideaboard`, `hcsr04`, `socketpool`, `espnow` |
| #4 | `config.py` único: cada rover se identifica por su **MAC** | IDs ArUco 10 y 11 decodificados de fotos de los stickers |
| #5 | Navegación, planificador, `ControladorRover` y **simulador físico** | 3 cubos entregados en ~30 s simulados |
| #6 | Herramientas de USB, `VISION_HOST` por `settings.toml`, README | `info_rover`, `respaldar_rover`, `probar_motores`, `desplegar` |
| #7, #10, #11 | Documentación de la Fase A (cámara) y guía de calibración | Calibración propia **omitida** a propósito |
| #8 | Tips de prueba y `FACTOR_VELOCIDAD` (0.5) | Velocidades de avance/empuje ajustables |
| #9 | LED de estado y **una sola `IdeaBoard` compartida** | Corrige un fallo real (ver abajo) |
| #12 | `desplegar.py` escribe con `open()` en vez de `mpremote fs cp` | Despliegue verificado por tamaño |
| #13 | LED en **IO33**, paleta sin rojo mezclado + parpadeos, `PIN_IR = None`, `probar_led.py` | Ver [§6](#6-indicador-led-para-probar-sin-cable) |

**Hallazgos que cambiaron el diseño** (todos descubiertos al tocar hardware real):

- Los rovers corren **CircuitPython 9.2.4**, no MicroPython: el esqueleto inicial hubo que reescribirlo.
- El umbral de agarre de 1 celda era irreal: el centro del rover nunca llega tan cerca del cubo (ahora 6).
- `Motores` y `Sensores` creaban cada uno su `IdeaBoard()`; **la segunda instancia falla en el rover** ("pin in use").
  Ahora hay una sola (`firmware/placa.py`) y un test que lo vigila.
- `mpremote fs cp` **falla en CircuitPython** con archivos que aún no existen en el rover; se reemplazó por un
  método propio que verifica el tamaño.
- El `board.NEOPIXEL` de la IdeaBoard (IO2) **no muestra nada**; el LED que responde está en **IO33**, con orden
  de colores GRB, y en el rover 1 el **rojo mezclado con otros colores se pierde**.
- El ESP32 **solo trabaja en 2.4 GHz** (medido con un escaneo desde el propio rover: solo ve canales 1–13).
- La numeración de `--indice` de la cámara **no coincide con el orden de los nombres** (la C270 es el índice 1).
- Los números de puerto COM **cambian** al reconectar: se identifica cada rover por UID/MAC.

---

## 3. Qué funciona y cómo se comprobó

### 3.1 Comprobado en hardware real

| Qué | Cómo se comprobó | Resultado |
|---|---|---|
| Lectura de los rovers por USB | `info_rover.py` | Versión, UID y MAC de ambos |
| Respaldo del contenido de fábrica | `respaldar_rover.py` | En `rover_original/` (solo lectura) |
| Motores | `exec` desde RAM, 40 % durante 1.5 s, con la persona viendo | `motor_1` = rueda izquierda, `motor_2` = derecha, ambas hacia adelante, en los dos rovers |
| ESP-NOW | Un rover escucha 12 s y el otro manda 5 mensajes; luego al revés | **5 de 5** en ambos sentidos, RSSI −22 a −31 dBm (corta distancia) |
| Banda de WiFi | Escaneo de redes desde el rover | Solo canales 1, 4, 7 y 10 → solo 2.4 GHz |
| WiFi + visión | Firmware desplegado, reinicio y lectura de lo que imprime | Ambos: `conectado a vision 192.168.51.119 2026`; la visión los lista como clientes (`192.168.51.8`, `192.168.50.193`): **misma red, sin aislamiento** |
| Cámara (Fase A) | Ventana en vivo y lectura del puerto 2026 | Ver tabla siguiente |
| LED en IO33 (rover 1) | Pruebas de colores con la persona viendo | Responde en IO33, orden GRB; rojo mezclado débil |

**Cámara y visión** (con la cámara real, 30-sep-2026):

| Comprobación | Resultado |
|---|---|
| Marcadores de esquina | `Esquinas 4 de 4`, en **orden horario**: 0 arriba-izquierda, 1 arriba-derecha, 2 abajo-derecha, 3 abajo-izquierda |
| Zonas y salida | Verde arriba, roja a la derecha, azul abajo, salida al centro del lado izquierdo |
| Coordenadas | Contando celdas desde el marcador 0 a mano, el cubo rojo dio col ≈ 20, igual que la visión |
| Sentido de los ejes | Cubo movido a la izquierda y hacia abajo: `col` bajó (34.3 → 23.3), `row` subió (24.2 → 39.6) ✔ |
| Veredicto de entrega | Cubo azul en (23.30, 39.57) → la visión lo marcó **EN POSICIÓN**; coincide con `mundo.cubo_en_su_zona` |
| Oclusión | Un cubo tapado quedó con `edad 10100 ms` (naranja): la visión conserva su última posición |
| Rovers 10 y 11, mirando a la derecha | `theta` **358.4° y 358.7°** (≈ 0°): el frente real coincide con el "adelante" del marcador |
| Rovers girados hacia arriba | `theta` **86.9° y 89.4°** → `theta` sube en sentido antihorario, como espera `navegacion.py` |
| Velocidad | La visión procesa a **~10 cuadros/s** a 1280×720 (publica a 20 Hz) |

### 3.2 Comprobado solo en simulación y tests

`cd pc_dev && python -m pytest -q` → **63 tests** (~2 s, sin hardware ni red):

| Archivo | Tests | Qué cubre |
|---|---|---|
| `test_ciclo_completo.py` | 11 | **Lazo cerrado:** los 2 rovers entregan los 3 cubos sin choques; con ruido de visión (0.15 y 0.3 celdas); no se mueven fuera de `RUNNING`; se detienen en `FINISHED` |
| `test_firmware_main.py` | 10 | Ejecuta `firmware/main.py` en la PC con hardware falso: config por MAC, motores, paro seguro, exige `VISION_HOST`, una sola `IdeaBoard`, LED en IO33 sin choque de pines, parpadeos con reloj falso |
| `test_maquina_estados.py` | 15 | Estados y transiciones (agarre, entrega por zona, cubo perdido) |
| `test_mundo.py` | 18 | Contrato v2, frescura, latencia, `cubo_en_su_zona` |
| `test_navegacion.py` | 9 | Geometría, control de rumbo, mezcla de ruedas |

El simulador (`pc_dev/simulador_fisico.py`) es **propio y simple**: círculos que se empujan, 6 celdas/s y 90°/s a
potencia máxima. **Esos números son inventados** y hay que reemplazarlos con lo medido (ver [§9](#9-plan-completo-lo-que-falta-paso-a-paso)).
No reemplaza al `mock_publisher.py` del repo guía (que publica telemetría realista pero no reacciona a los rovers).

---

## 4. Los rovers: hardware y datos medidos

| | Rover 1 | Rover 2 |
|---|---|---|
| ID ArUco (sticker, diccionario 4X4) | **10** | **11** |
| MAC (radio WiFi / ESP-NOW) | `E0:8C:FE:25:C7:48` = `(224,140,254,37,199,72)` | `E0:8C:FE:27:A6:78` = `(224,140,254,39,166,120)` |
| UID de la placa | `0EC8EF527C84` | `0EC8EF726A87` |
| Puerto USB en la última sesión | `COM12` | `COM3` (**cambian**: identificar por UID/MAC) |
| Colores asignados (fijo por ahora) | rojo, azul | verde |
| Placa / firmware | CRCibernetica **IdeaBoard (ESP32)**, CircuitPython 9.2.4 | igual |

**Pines:**

| Función | Pin / detalle | Comprobado |
|---|---|---|
| Motor 1 (**rueda izquierda**) | IO12 / IO14 | ✅ |
| Motor 2 (**rueda derecha**) | IO13 / IO15 | ✅ |
| **LED de estado (NeoPixel)** | **IO33**, orden GRB | ✅ rover 1 · ⏳ rover 2 |
| Ultrasónico HCSR04 | TRIG IO26, ECHO IO25 (código de fábrica) | ⏳ sin probar |
| Infrarrojo | El ejemplo de fábrica lo pone en IO33 (el pin del LED): **no se usa** (`PIN_IR = None`) | — |
| `board.NEOPIXEL` de la IdeaBoard | IO2 — **no muestra nada** en estos rovers | ✅ |
| IMU | I2C, librería `adafruit_lsm6ds` | ⏳ sin integrar |
| Sensor de color | I2C (Qwiic) | ⏳ sin integrar |

Librerías ya en `/lib` de ambos: `ideaboard`, `hcsr04`, `adafruit_motor`, `adafruit_lsm6ds`, `neopixel`, `simpleio`,
`adafruit_requests`, etc. **Contenido de fábrica:** `code.py` (prueba de LED), `prueba.py` (LED + motores + I2C) y
`examples/`; el `code.py` del rover 2 era `print('standby, sin wifi')` con un bucle infinito. Ninguno traía código
de coordinación ni de sensores propio.

---

## 5. Cómo nos conectamos a los rovers

Se habla con los rovers **por el cable USB**, sin Thonny, con **`mpremote`**; Claude Code simplemente corre los
comandos en la terminal de la PC.

**Preparación (una vez por PC):** `pip install --user mpremote` y listar con `python -m mpremote connect list`.
Siempre `python -m mpremote ...` (el ejecutable queda fuera del PATH). **Cerrar Thonny** (un puerto no se comparte).
Para mover motores hace falta además encender la batería de motores (el USB solo alimenta la lógica).

| Herramienta (`herramientas/`) | Qué hace | ¿Mueve algo? |
|---|---|---|
| `python herramientas/info_rover.py` | Lista los rovers y muestra versión, UID y MAC | No |
| `python herramientas/respaldar_rover.py COM12 rover1` | Copia los archivos propios del rover a `rover_original/rover1/` | No |
| `python herramientas/probar_motores.py COM12 --ruedas-en-el-aire` | Gira cada motor 1.5 s al 40 % | **Sí**: levantar el rover y encender baterías; se niega sin el flag |
| `python herramientas/probar_led.py COM12` | Recorre los estados del LED (`--segundos`, `--estados a,b`) | No (interrumpe el firmware; reiniciar el rover después) |
| `python herramientas/desplegar.py COM12` | Muestra qué copiaría | No (simulación) |
| `python herramientas/desplegar.py COM12 --si` | Copia `comun/` + `firmware/` y **reemplaza `/code.py`** | Escribe en el rover. Si el cable se suelta a mitad, **repetir el despliegue completo** |

<details>
<summary><b>Comandos sueltos útiles y cómo se despliega paso a paso</b></summary>

```bash
# Ejecutar código en el rover desde RAM (no guarda nada)
python -m mpremote connect COM12 exec "import wifi; print(list(wifi.radio.mac_address))"

# Consola en vivo (ver los print del firmware). Salir con Ctrl-]
python -m mpremote connect COM12 repl
```

**Desplegar a un rover (con USB y las ruedas en el aire):**
1. `python herramientas/info_rover.py` → identificar el rover por UID (no por el COM).
2. `python herramientas/respaldar_rover.py <COM> <rover1|rover2>` (solo la primera vez).
3. Crear `firmware/settings.toml` (Git lo ignora) a partir de `settings.toml.example`, con el WiFi, la contraseña y
   `VISION_HOST` = IP de la PC de visión (`ipconfig`). **Nunca** escribir la contraseña en el `.example`.
4. `python herramientas/desplegar.py <COM> --si` (debe terminar en `Listo` sin `ERROR`) y copiar el `settings.toml`
   al rover con `_rover.subir` o `mpremote`.
5. Reiniciar el rover y abrir `python -m mpremote connect <COM> repl`: debe imprimir
   `rover 10|11 conectando WiFi...` y `conectado a vision <IP> 2026`.

CircuitPython arranca `code.py` solo al dar energía: tener las ruedas en el aire. Sin `VISION_HOST` el firmware
aborta con un mensaje y deja los motores frenados.
</details>

---

## 6. Indicador LED (para probar sin cable)

Para las pruebas en el suelo los rovers van **sin cable a la PC** (autonomía del reto, y el cable se enreda). Sin USB
no hay REPL ni `print`, así que un LED dice qué hace el rover (`firmware/indicador.py`).

**Medido:** el LED que responde es un **NeoPixel en IO33**, orden **GRB**. El rojo mezclado se pierde en el LED del
rover 1, así que la paleta usa solo **verde, azul, cian, blanco y rojo puro**: la familia de color dice qué pasa y el
**parpadeo** dice la etapa.

| LED | Significa |
|---|---|
| 🔵 Azul **parpadeo rápido** | Conectando al WiFi / a la visión |
| 🔵 Azul **fijo** | Conectado; esperando que la ronda pase a `RUNNING` (**no se mueve**) |
| 🟢 Verde **lento** | `APROXIMAR` (yendo a ubicarse detrás del cubo) |
| 🟢 Verde **rápido** | `SUJETAR` (empujando hasta confirmar que lleva el cubo) |
| 🟢 Verde **fijo** | `TRANSPORTAR` (empujando el cubo al depot) |
| 🩵 Cian **fijo** | `ENTREGAR` (soltó el cubo, retrocede) |
| 🩵 Cian **lento** | `BUSCAR` (sin cubo fresco que atender) |
| ⚪ Blanco **fijo** | `OCIOSO` (terminó su cola de colores) |
| ⚪ Blanco **lento** | `DETENIDO` (ronda terminada, `FINISHED`) |
| 🔴 Rojo **lento** | Dejó de llegar telemetría: motores frenados |
| 🔴 Rojo **fijo** | **Error** (p. ej. falta `VISION_HOST`): motores frenados. Conectar el USB y leer el mensaje con `repl` |

Lento = 1 Hz, rápido = 4 Hz. Al cambiar de estado el LED empieza encendido.

**Qué se vio con los ojos:** con la paleta **anterior** en el rover 1 se vieron bien `esperando` (azul), `error`
(rojo), `BUSCAR` (morado), `APROXIMAR` (azul) y `OCIOSO` (blanco); los estados que mezclan rojo se vieron menos de lo
esperado y de ahí salió esta paleta. **⚠️ La paleta nueva con parpadeos aún no se ha visto con los ojos**
(`python herramientas/probar_led.py <PUERTO>`), y el pin del LED del **rover 2 no está confirmado**.

**Antes de quitar el cable:** confirmar que la placa **enciende con las baterías** (no sabemos si la batería de
motores también alimenta la lógica), que `settings.toml` está copiado y que las ruedas están en el aire para el
primer arranque sin USB. La PC de visión debe seguir encendida y en la misma red.

---

## 7. Cómo correr cada cosa

| Quiero… | Comando |
|---|---|
| Correr los tests | `pip install -r pc_dev/requirements.txt` y luego `cd pc_dev && python -m pytest -q` |
| Ver una corrida simulada (estados y choques) | `python pc_dev/trazar_simulacion.py [ruido] [segundos]` |
| Ver la decisión contra telemetría de un publisher | `python pc_dev/ejecutar_simulacion.py --host 127.0.0.1 --port 2026 --id 10` (el mock no reacciona a las ruedas) |
| Levantar el publisher simulado del repo guía | `python contrato/mock_publisher.py` en `.../guia/vision-system/` (déjalo en una terminal interactiva; con `ready` pasa a `READY` y a los 60 s a `RUNNING`) |
| Levantar la visión real con la cámara | Ver [§11](#11-guía-de-la-cámara-y-el-sistema-de-visión) |
| Desplegar a un rover | Ver [§5](#5-cómo-nos-conectamos-a-los-rovers) |

---

## 8. Lo que falta: por comprobar, calibrar y construir

### 8.1 Ya existe pero **no lo hemos visto funcionar** (por comprobar)

| Qué | Cómo comprobarlo |
|---|---|
| Despliegue completo del rover 2 | Repetir `desplegar.py --si`; sin `ERROR` y con los 18 archivos verificados |
| Paleta del LED con parpadeos (ambos rovers) | `probar_led.py` en cada uno |
| Pin del LED en el rover 2 | Si no es IO33, probar IO2 / IO32 una por una; el pin podría ser distinto por rover (tabla por MAC en `config.py`) |
| Que la placa **enciende con baterías**, sin USB | Desconectar el USB con las baterías puestas y mirar el LED |
| El firmware completo **moviendo ruedas**, con telemetría real | Fase C del plan |
| `READY` → `RUNNING` y los estados del FSM con telemetría real | Fase C |
| Que el estimador de latencia no descarte mensajes buenos por WiFi real | Fase C: el rover debe reaccionar y no quedarse en LED rojo lento |
| Que ESP-NOW convive con la conexión WiFi (mismo canal que el router) | Antes de usarlo en `main.py` (Fase F) |
| Ultrasónico: dónde apunta y a qué distancia detecta el cubo | Leer el sensor con un cubo a 1, 2, 3… cuadros |
| Que la cámara de la competencia venga calibrada | Preguntar a los organizadores |

### 8.2 Números hoy inventados (por calibrar)

- Velocidad lineal y de giro reales por rover vs. potencia (el simulador asume 6 celdas/s y 90°/s) y la **potencia mínima**
  a la que las ruedas arrancan; diferencia entre los dos motores (`_factor_izq/_factor_der` en `motores.py`).
- `DISTANCIA_AGARRE_CM` (4 cm) en `config.py`.
- Constantes de `comun/planificador.py` (preagarre, rodeo, velocidades) y umbrales de `comun/maquina_estados.py`.
- Offset entre el centro del marcador ArUco y el centro real del chasis.
- Geometría real de las paletas (el modelo asume que el cubo se empuja de frente).

### 8.3 Funciones que faltan (por construir)

- **Rampa de aceleración** (hoy los arranques son bruscos; solo existe `FACTOR_VELOCIDAD = 0.5`).
- **Negociación rover↔rover por ESP-NOW**: reclamar/liberar colores tolerando mensajes perdidos, reasignación dinámica
  (que un rover ayude al otro al terminar), confirmar recolección y entrega. El firmware ya puede enviar/recibir
  (`comm_espnow.py`, probado) pero `main.py` **no lo usa**.
- **Evitación de colisiones robusta**: hoy el rover de id mayor cede el paso y el de id menor frena de emergencia (≤ 2
  roces por corrida en el simulador con ruido alto). El campo de repulsión existe (`navegacion.repulsion`) pero está
  apagado porque empeoraba el empuje.
- **Información imperfecta**: hoy un cubo no fresco manda al rover a `BUSCAR` (quieto); falta navegar a la última posición
  conocida o un patrón de búsqueda.
- **Sensor de color** (agarre/entrega más fiables que solo el ultrasónico) e **IMU** (mantener rumbo entre cuadros de
  visión; hoy el control es proporcional sobre el `theta` de la visión, sin PID).
- **Botón de arranque** de la IdeaBoard (hoy arranca solo al ver `RUNNING`).
- **Obstáculos** (el campo existe en el contrato, pero la primera edición va vacío).

### 8.4 Decisiones y preguntas abiertas

- ¿Qué **red** se usa en la competencia? Hoy `Visitas` (2.4 GHz). Plan B: un hotspot o router propio de 2.4 GHz.
- ¿La cámara del reto viene **calibrada**? (Se asumió que sí; si no, ver la guía de calibración en la §11.)
- ¿Cómo se monta la cámara (soporte, altura) para ver siempre los 4 marcadores completos? ¿La cancha, los marcadores y
  los cubos de 6 cm ya están armados?
- ¿Cuándo se hace el PR `develop → main`? (No hay fecha: se decide cuando haya una versión estable.)

---

## 9. Plan completo: lo que falta, paso a paso

**Reglas de seguridad para todo el plan:** un cambio por prueba · ruedas en el aire hasta terminar la Fase C · una mano
junto al interruptor de la batería de motores · `f` (stop) en la ventana de la visión · mantener `FACTOR_VELOCIDAD = 0.5`
hasta tener 3 corridas limpias · el firmware frena solo si se pierde la telemetría > 0.5 s.

### Fase A — Cámara y sistema de visión · ✅ completa

| # | Qué | Estado |
|---|---|---|
| A1 | Clonar e instalar el sistema de visión (repo guía, sin modificarlo) | ✅ |
| A2 | `verificar_geometria` → `RESULTADO GENERAL: TODO OK` | ✅ |
| A3 | Mock + `test_client` sin cámara | ✅ |
| A4 | Montar la cancha y reubicar la cámara hasta ver los 4 marcadores | ✅ |
| A5 | Elegir la cámara (`--indice 1`) | ✅ |
| A6 | Calibración propia de la cámara | ⏭️ omitida (guía en la §11) |
| A7 | Vista en vivo: orden horario, zonas, ejes, grilla | ✅ |
| A8 | Detección de los rovers 10 y 11 con su `theta` | ✅ |

### Fase B — Rovers conectados a la visión, sin mover ruedas · casi completa

| # | Qué hacer | Resultado esperado | Estado |
|---|---|---|---|
| B1 | Red de 2.4 GHz compartida entre la PC y los rovers | Los rovers ven a la PC | ✅ `Visitas` |
| B2 | `settings.toml` en cada rover (WiFi + `VISION_HOST`) | Copiado a ambos | ✅ |
| B3 | Respaldar el contenido de fábrica | `rover_original/` | ✅ |
| B4 | Desplegar el firmware al rover 1 | 18 archivos verificados; `conectado a vision` | ✅ |
| B5 | **Repetir el despliegue del rover 2** | `desplegar.py --si` termina en `Listo`, sin `ERROR` | ⏳ |
| B6 | Reiniciar ambos y mirar `repl` | `conectado a vision…`; la visión muestra 2 clientes | ⏳ (repetir tras B5) |
| B7 | `probar_led.py` en ambos | Se ve la paleta; si el rover 2 no responde en IO33, probar IO2/IO32 | ⏳ |
| B8 | Arrancar con baterías, **sin USB** | LED azul fijo; la placa enciende sin cable | ⏳ |

### Fase C — Primer movimiento (ruedas en el aire)

| # | Qué hacer | Resultado esperado | Estado |
|---|---|---|---|
| C1 | Rovers levantados, baterías de motores encendidas, USB conectado; cubos puestos; en la visión `r` (ready) y esperar 60 s | Pasa a `RUNNING`; rover 10 se orienta al cubo **rojo** y rover 11 al **verde** (LED verde lento) | ⏳ |
| C2 | Revisar el sentido de giro y de avance | Cada rover gira hacia su cubo; si gira al revés, revisar `INVERTIR_IZQ/DER` | ⏳ |
| C3 | Frenado | `f` (stop) y `FINISHED` paran las ruedas (LED blanco lento); sin telemetría 0.5 s → paro y LED rojo lento | ⏳ |
| C4 | Repetir **sin USB**, con el LED como única pista | Mismo comportamiento | ⏳ |
| C5 | Revisar la latencia con WiFi real | No hay mensajes descartados por error ni LED rojo lento espurio | ⏳ |

### Fase D — Calibración en el suelo (contando cuadros; ver [§10](#10-tips-para-que-funcione-mejor))

| # | Qué medir | Qué se ajusta | Estado |
|---|---|---|---|
| D1 | Potencia mínima a la que arrancan las ruedas | `FACTOR_VELOCIDAD` (hay que anotar el valor) | ⏳ |
| D2 | Velocidad lineal (cuadros ÷ segundos) a 0.5, 0.7 y 1.0 | `VEL_MAX` del simulador | ⏳ |
| D3 | Giro en el sitio (grados/s con `theta` de la visión) | `GIRO_MAX` del simulador | ⏳ |
| D4 | Desvío al ir "recto" 20 cuadros | `_factor_izq/_factor_der` en `motores.py` | ⏳ |
| D5 | Offset marcador ↔ centro del chasis | Corrección en la lógica si hace falta | ⏳ |
| D6 | Ultrasónico: dónde apunta y a qué distancia ve el cubo | `DISTANCIA_AGARRE_CM` | ⏳ |
| D7 | Actualizar constantes y simulador con lo medido; correr `pytest` | Tests siguen en verde | ⏳ |
| D8 | Implementar la rampa de aceleración | Arranques suaves | ⏳ |

Anotar cada medición (rover, potencia, cuadros, segundos) en `docs/calibracion.md` para no repetirlas.

### Fase E — Pruebas en cancha, escalonadas

| # | Prueba | Éxito | Estado |
|---|---|---|---|
| E1 | **Un rover, un cubo**, el otro apagado o fuera; cubo y depot cercanos | La visión marca el cubo **EN POSICIÓN**; el rover retrocede | ⏳ |
| E2 | Un rover con su cola completa (rover 10: rojo y azul) | Entrega los dos | ⏳ |
| E3 | Los dos rovers, cada uno con su color, cubos lejos entre sí | Sin cruces ni roces | ⏳ |
| E4 | Escenario completo (3 cubos, salida a la izquierda) | Los 3 entregados; medir el tiempo con el acta de la visión (`vision/actas/`) | ⏳ |

Ante un fallo: anotarlo, **reproducirlo en `simulador_fisico.py`**, corregir, `pytest`, redesplegar.

### Fase F — Lo complicado (cada uno con tests en el simulador **antes** de ir al robot)

| # | Qué | Estado |
|---|---|---|
| F1 | Negociación por ESP-NOW + reasignación dinámica (primero verificar que ESP-NOW convive con el WiFi) | ⏳ |
| F2 | Evitación de colisiones robusta | ⏳ |
| F3 | Información imperfecta: navegar a la última posición conocida / búsqueda | ⏳ |
| F4 | Sensor de color para agarre y entrega | ⏳ |
| F5 | IMU + PID para el rumbo | ⏳ |
| F6 | Botón de arranque de la IdeaBoard | ⏳ |
| F7 | Obstáculos (solo si vuelven en una edición futura) | ⏳ |

### Fase G — Entrega y competencia

| # | Qué | Estado |
|---|---|---|
| G1 | Documentación técnica y código fuente entregables (el reto lo exige) | ⏳ |
| G2 | Registro del costo de los componentes adicionales (el reto lo exige) | ⏳ |
| G3 | Ensayo completo y autónomo, sin intervención humana (demostración) | ⏳ |
| G4 | Plan B de red (hotspot/router propio 2.4 GHz) y lista de verificación del día de la competencia | ⏳ |
| G5 | PR `develop → main` cuando el equipo decida la versión estable | ⏳ |

---

## 10. Tips para que funcione mejor

<details>
<summary><b>Contar cuadros: la cancha es su propia regla</b> (1 cuadro = 1 celda = 20 mm)</summary>

| Qué quieres saber | Cómo contar | Qué debe dar |
|---|---|---|
| ¿La cancha está bien montada? | Contar cuadros **de centro a centro** de dos marcadores de esquina vecinos | **43 cuadros** (860 mm). El tablero físico tiene 50×50, pero el área de juego es 43×43. Si da otro número, el montaje está mal; no ajustar el código para compensar |
| ¿La visión ubica bien? | Poner un cubo/rover en un cuadro conocido, contar desde el **centro del marcador 0** y comparar con `test_client.py` o la ventana | ≤ 1 cuadro de diferencia. Si `col` no sube al ir a la derecha o `row` al ir hacia abajo, los marcadores están en orden equivocado |
| ¿Qué tan rápido va el rover? | Marcar un cuadro de salida, avanzar con potencia fija un tiempo medido y **contar cuadros**; velocidad = cuadros ÷ segundos; 3 veces y promediar | Anotar por rover y por potencia; comparar con el simulador (6 celdas/s) |
| ¿Se desvía al ir "recto"? | Avanzar 20 cuadros y contar cuántos **de lado** se corrió | ≈ 0; si siempre al mismo lado, ajustar `_factor_izq/_factor_der` |
| ¿Cuánto gira? | Girar en el sitio un tiempo fijo y leer `theta` antes y después | Grados/s por rover (el simulador asume 90°/s) |
| ¿A qué distancia ve el cubo el ultrasónico? | Cubo a 1, 2, 3… cuadros del frente (mide 3 cuadros de lado) | Fija `DISTANCIA_AGARRE_CM` |
</details>

<details>
<summary><b>Movimientos muy suaves primero, optimizar después</b></summary>

- **Orden de pruebas, de menos a más riesgo:** ruedas en el aire → suelo, espacio libre, sin cubos → un cubo con un
  solo rover → los dos. No pasar al siguiente hasta repetir 3 veces el actual sin fallos.
- **`FACTOR_VELOCIDAD`** en `firmware/config.py` (hoy **0.5**) multiplica las velocidades de avance y de empuje.
  Subirlo de 0.1 en 0.1, solo tras 3 corridas limpias. Si a un valor bajo las ruedas ni arrancan, el motor tiene una
  **potencia mínima**: subir hasta que arranque y anotarla.
- **Cambiar una sola cosa por prueba** y anotar qué se cambió.
- **Lo que el factor NO suaviza:** los giros en el sitio (`w_max` y su piso en `comun/navegacion.py`) y la marcha atrás
  (`VEL_RETROCESO` en `comun/planificador.py`); tampoco hay rampa de aceleración todavía.
- **Siempre una forma de cortar:** interruptor de la batería de motores, `f` (stop) en la visión, `Ctrl-C` en el `repl`.
- **Empuje suave = el cubo no se escapa:** en el simulador, el fallo más común es el cubo que resbala de lado.
- **Cuando funcione a baja velocidad:** subir el factor hacia 1.0, reducir distancias de preagarre/rodeo, recalibrar el
  simulador con lo medido y volver a correr `pytest`.
</details>

---

## 11. Guía de la cámara y el sistema de visión

Usamos el **sistema de visión del repo guía, sin modificarlo**: está clonado en `C:/Users/Allis/Documents/guia`, y lo
único que se agregó ahí es la carpeta `.venv` (que su `.gitignore` ignora). Solo lo ejecutamos y leemos lo que publica.

**Levantar la visión con la cámara real:**

```bash
cd C:/Users/Allis/Documents/guia/vision-system
set PYTHONIOENCODING=utf-8        # cmd; en PowerShell: $env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python -m vision.sistema --indice 1 --camara logitech_c270 --ventana
```

La ventana permite `r` (ready), `f` (stop), `a` (abort), `q` (salir). De `READY` a `RUNNING` pasa solo tras la
preparación (60 s por defecto). Mientras no vea **los 4 marcadores de esquina completos** no publica rovers ni cubos.
**Solo un programa puede usar la cámara a la vez.**

<details>
<summary><b>Qué hay que tener para la cámara y la cancha</b></summary>

| Qué | Estado |
|---|---|
| Webcam USB externa (Logitech C270, `--indice 1`) | ✅ detectada y funcionando |
| Soporte cenital: el repo guía trae `archivos_fabricacion/WebCam Base.stl` (impresión 3D, 4 tornillos con tuerca de 3/16" y 1 de 1/4", de 2 cm); un trípode sirve para probar | Por definir |
| Cancha de 1 m × 1 m cuadriculada (celdas de 2 cm) | Armada para las pruebas |
| 4 marcadores de esquina (IDs 0–3, de 10 cm, con margen blanco; `aruco/aruco_id0..3_negro10cm.pdf` impresos al 100 %) | Puestos y detectados |
| Cubos de 6 cm rojo, verde y azul | En uso |
| Stickers ArUco 10 y 11 en los rovers | Pegados y detectados |
</details>

<details>
<summary><b>Calibración propia de la cámara (omitida por ahora; guía por si hace falta)</b></summary>

**Decisión (30-sep-2026): no se calibra por ahora**, porque se espera que la cámara del reto venga calibrada. Se usó el
perfil que ya trae el repo (`logitech_c270`), aceptado como *compatible*. Si más adelante las posiciones salen corridas o
se cambia de cámara, esta es la guía (detalle en `vision-system/PUESTA_A_PUNTO.md` del repo guía).

> **El repo guía no se modifica.** La herramienta guarda el perfil en `vision-system/vision/calibraciones/<nombre>.json`.
> Para no pisar el `logitech_c270.json` que trae el repo, **usar un nombre propio**, p. ej. `"NullPointer C270"`.

Materiales: impresora, regla con mm, cartón o tabla lisa, pegamento (en **toda** la superficie), tijeras. Los PDF ya
están en [`calibracion/`](calibracion/) (`patron.pdf` y `marcador_prueba.pdf`).

1. **Imprimir al 100 % de escala** (nunca "ajustar a la página") y **medir con la regla la línea de 100 mm** de cada hoja.
2. **Armar el patrón**: cortar una hoja por la línea gris, pegarlas **a tope** y sobre cartón rígido, **plano**.
3. **Cerrar la visión** (`q`): la cámara solo la usa un programa a la vez.
4. **Calibrar**: `.venv\Scripts\python -m vision.tools.calibrar_camara --indice 1 --camara "NullPointer C270"`;
   mostrar el patrón en las 9 zonas del cuadro, 3 distancias y ≥ 4 vistas inclinadas; seguir la línea `>` del panel;
   cuando diga "ya alcanza", apretar `C`. **EXCELENTE/BUENA** sirven; **MALA** no guarda el perfil.
5. **Verificar a ojo**: `... calibrar_camara --verificar --indice 1 --camara "NullPointer C270"`.
6. **Medir la precisión**: `... precision_ubicacion --camara "NullPointer C270"`.
7. **Usar el perfil nuevo**: lanzar la visión con `--camara "NullPointer C270"` y repetir la comprobación de los rovers.
</details>

---

## 12. Problemas conocidos y soluciones

<details>
<summary><b>Ver la tabla completa</b> (Windows, mpremote, rovers, red, cámara)</summary>

| Síntoma | Causa y solución |
|---|---|
| `python` abre la Microsoft Store o "no está instalado" | El alias de la Store intercepta `python.exe`. Desactivar los alias de `python.exe`/`python3.exe` (Configuración → Aplicaciones → Alias de ejecución) o llamar al intérprete real por ruta |
| `pip install mpremote` falla con `WinError 2 ... pyserial-miniterm.exe.deleteme` | Sin permisos en `C:\Python312\Scripts`. Usar `pip install --user mpremote` y ejecutarlo como `python -m mpremote` |
| `mpremote` → `could not enter raw repl` | El rover corre un `code.py` con bucle infinito. Mandar Ctrl-C por serial (las herramientas del repo lo hacen solas) |
| `mpremote` no ve el puerto / "access denied" | Thonny u otro programa tiene el puerto abierto. Cerrarlo |
| Los números de COM cambian entre conexiones | Identificar cada rover por **UID/MAC** (`info_rover.py`), no por el COM |
| `mpremote fs cp` falla con `OSError: [Errno 2]` al copiar al rover | En CircuitPython falla si el destino **aún no existe**. `desplegar.py` ya no lo usa: escribe con `open()` desde un `exec` y verifica el tamaño |
| `fs ls` de mpremote da error `ilistdir` | CircuitPython no lo soporta; listar con `os.listdir` vía `exec` |
| Despliegue interrumpido (cable suelto) | El rover queda con archivos mezclados o truncados. **Repetir `desplegar.py --si` completo** |
| `IdeaBoard` falla con "pin in use" | Se creó la placa dos veces. Todo el firmware la pide por `firmware/placa.py` |
| El LED no se enciende con `board.NEOPIXEL` | En estos rovers ese pin (IO2) no muestra nada; el LED está en IO33 (`config.PIN_LED`) |
| El firmware se cae al arrancar por el pin IO33 | IO33 es el LED; no usarlo para otro periférico (`PIN_IR = None`) |
| `e.send(...)` de ESP-NOW devuelve falsy aunque el mensaje llegó | Es normal en CircuitPython: verificar del lado receptor |
| El firmware aborta con `Falta VISION_HOST` | Falta `VISION_HOST` en el `settings.toml` del rover (LED rojo fijo) |
| `RuntimeError: MAC desconocida` al arrancar | Placa distinta a las dos registradas: agregar su MAC a `ROVERS` en `firmware/config.py` |
| El rover no conecta al WiFi | Red de 5 GHz (usar 2.4), SSID/clave mal escritos en `settings.toml`, o la PC está en otra red |
| El rover conecta pero no recibe telemetría | Firewall de Windows bloqueando el puerto 2026, o IP equivocada (la IP de la PC cambia al cambiar de red) |
| Dejé la contraseña del WiFi en `settings.toml.example` | Ese archivo **se sube al repo**. Mover los datos a `firmware/settings.toml` (ignorado) y `git checkout -- firmware/settings.toml.example`. Si ya se subió, cambiar la clave en el router |
| `git clone` falla con `Filename too long` | Clonar en una ruta corta, p. ej. `C:\Users\<usuario>\Documents\Null-Pointer` |
| Los PDF se dañan al clonar en Windows | Marcados como binarios en `.gitattributes` |
| `mock_publisher.py` se cierra solo / `test_client` da `WinError 10061` | El mock lee comandos por stdin y termina si no hay entrada. Correrlo en una terminal normal y esperar ~3 s |
| `vision.sistema` se cae con `UnicodeEncodeError ... '✓'` | Definir `PYTHONIOENCODING=utf-8` antes de lanzarlo |
| `diagnostico_camara --listar` no muestra la webcam externa | No está conectada o Windows no le dio permiso. Conectarla y repetir |
| La cámara muestra la imagen negra | Índice equivocado: el orden de los nombres no coincide con `--indice` (la C270 es el 1). Confirmar **mirando la imagen** |
| La visión no publica rovers ni cubos | No ve los 4 marcadores de esquina completos: reubicar la cámara |
| Un rover recién puesto tarda en aparecer | La visión exige ~5 cuadros estables (~0.5 s); también descarta solas las detecciones falsas sobre la cuadrícula |
</details>

---

## 13. Flujo de trabajo con git

- `main`: vacía a propósito por ahora (solo el commit inicial). **No hay PR a `main` todavía.**
- `develop`: rama de integración; todo entra por PR (#1–#13 ya fusionados, sin ramas ni PRs pendientes).
- Ramas de trabajo: `feat/...`, `fix/...`, `chore/...`, `docs/...`, siempre contra `develop`.
- Commits con `Co-Authored-By` cuando los escribe Claude Code.
- **Este README es la memoria del proyecto:** todo lo importante (decisiones, hallazgos, pruebas hechas y su resultado,
  cambios de plan, problemas y soluciones) se agrega aquí, en el mismo PR que lo origina.
- **El repo guía no se modifica** (`C:/Users/Allis/Documents/guia`): solo se ejecuta y se lee lo que publica.
- **Antes de escribir en un rover** (desplegar, reemplazar su `code.py`, copiar archivos) se confirma con el equipo; antes de
  desplegar siempre hay respaldo en `rover_original/`.
- **Las contraseñas las escribe una persona** en `firmware/settings.toml`; nunca se leen, se muestran ni se suben.
- **Nunca subir:** `firmware/settings.toml` (WiFi), `fotos/` (capturas de la cámara). Ambos están en `.gitignore`.

---

## 14. Referencias

- Repo guía del reto (reglas, specs, sistema de visión): [Vision-Rover-Challenge](https://github.com/Universidad-Cenfotec/Vision-Rover-Challenge)
  — `el_reto.md`, `robot.md`, `reglamento.md`, `vision-system/contrato/CONTRATO.md`, `codigos/` (ejemplos de PID,
  IMU, color y ESP-NOW que aún no adaptamos).
- Protocolo de telemetría (resumen propio): [`docs/contrato_telemetria.md`](docs/contrato_telemetria.md)
- Arquitectura y decisiones: [`docs/arquitectura.md`](docs/arquitectura.md)
- Firmware y despliegue: [`firmware/README.md`](firmware/README.md)
- Simulación: [`simulacion/README.md`](simulacion/README.md)
