# Notas de banco: sensores y ESP-NOW (rescatadas de `fix/protocolo-v2`)

Observaciones hechas en banco con otros dos rovers (puertos COM6 y COM7) mientras
`develop` se desarrollaba en paralelo. **No son codigo ni cambian nada**: son datos
para contrastar con `firmware/config.py` y `firmware/sensores.py` actuales. Todo lo
de aqui hay que re-verificar en los rovers de `develop` (COM3 / COM12).

## Pines que NO coinciden con `firmware/config.py`

| Dato | `develop` (ejemplo de fabrica) | Medido en banco (COM6/COM7) |
|---|---|---|
| Ultrasonico | `TRIG=IO26`, `ECHO=IO25` | `TRIG=IO25`, `ECHO=IO26` (jumper SELECT-Vin puesto) |
| Infrarrojos (analogicos, 4x) | `PIN_IR = None` (no se usa) | `IO36`, `IO39` (adelante izq/der), `IO34`, `IO35` (atras izq/der) |

Si el ultrasonico no lee, probar con TRIG/ECHO intercambiados.

## IMU

Un escaneo I2C (Qwiic) solo encontro el LSM6DS3TRC en `0x6B`. No hay chip de color por I2C.

## Sensor de luz / color (modulo VCC/DI/AO/GND)

- Es un NeoPixel (DI) + fototransistor analogico (AO). **No distingue color** de forma
  confiable, solo presencia: cualquier objeto reflectante pegado cambia la lectura.
- Presencia de cubo: encender blanco vs apagado y comparar. Con cubo a distancia de
  agarre el cambio fue > 1500 (escala 16 bits); un umbral de ~800 queda comodo.
- Patron de color (solo si se quisiera confirmar el color agarrado, requiere distancia
  fija para calibrar): promediando R y G, un cubo rojo oscurece mucho, uno verde
  aclara mucho, uno azul casi no cambia.
- El diagrama oficial dice DI->IO32, AO->IO4, pero el NeoPixel real estaba en IO33
  (consistente con `PIN_LED = "IO33"` de `develop`).
- El modulo de color de uno de los robots de banco (COM7) parecia danado: canal verde del
  NeoPixel apagado y fototransistor sin lectura util en IO4/IO32/IO27. Revisar
  fisicamente cada modulo antes de confiar en un `cubo_sujeto()` basado en luz.

## Motores

Con el driver de la IdeaBoard, `motor_1` (IO12/IO14) y `motor_2` (IO13/IO15) giran en
ambas direcciones con el jumper SELECT-Vin puesto. El USB de la PC solo no alcanza para
moverlos: hace falta la bateria del robot.

## ESP-NOW: fijar el canal

`firmware/comm_espnow.py` de `develop` no fija canal. En banco, para que ambos rovers
terminaran en el mismo canal sin asociarse a ningun WiFi, hizo falta:

```python
wifi.radio.start_ap(" ", "", channel=6, max_connections=0)
wifi.radio.stop_ap()
# luego: espnow.Peer(mac=..., channel=6)
```

Sin esto (o con el WiFi de vision ya conectado en otro canal) los mensajes no llegaban.
Si ESP-NOW falla entre los dos rovers de `develop`, probar esto.

## MAC cruzadas

En banco las MAC anotadas quedaron cruzadas respecto a que robot era cual y ESP-NOW no
funcionaba hasta corregirlo. Confirmar en la consola de cada robot, juntas:

```python
import wifi, microcontroller
print("UID:", [hex(b) for b in microcontroller.cpu.uid])
print("MAC:", tuple(wifi.radio.mac_address))
```
