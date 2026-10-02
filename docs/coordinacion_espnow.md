# Coordinación de los dos rovers — 1 de octubre de 2026

El mismo código `comun/` y `firmware/` se copia a ambas IdeaBoard con
CircuitPython. COM3 corresponde al rover 1 y COM4 al rover 2 en esta sesión.
El puerto USB no determina la identidad durante la competencia.

## Identidad y elección

`config.ROVERS` vincula la MAC de cada placa con su marcador ArUco:

| Rover | Puerto | MAC registrada | ArUco |
|---|---|---|---|
| 1 | COM3 | E0:8C:FE:25:C7:48 | 10 |
| 2 | COM4 | E0:8C:FE:27:A6:78 | 11 |

`mac48()` convierte los seis bytes a un entero sin signo de 48 bits, en orden
de red: `valor = (valor << 8) | byte`. El entero mayor lidera: con esta tabla,
el rover 2. Ambos intercambian su identidad por ESP-NOW y verifican que reciben
al compañero configurado. Una placa desconocida no arranca el control.
La MAC no permite deducir el ArUco: si se cambia un sticker o una placa hay que
actualizar la tabla compartida. Ambas MAC se verificaron físicamente por USB
en COM3 y COM4 durante el despliegue.

## Reparto por distancia

1. Ambos reciben directamente la telemetría TCP de la cámara, puerto 2026.
2. El líder considera los cubos frescos todavía fuera de su zona del mismo color.
3. Ordena las parejas rover–cubo por distancia euclidiana entre centros.
   Reserva la pareja más cercana; el otro rover toma su cubo más cercano entre
   los restantes. Empates: ID ArUco y luego nombre del color.
4. El plan contiene como máximo un color por rover, sin duplicados. Se conserva
   durante aproximación, empuje y entrega, aunque cambien las distancias.
5. Cuando ambos terminan sus encargos, vuelve a comparar sus posiciones actuales:
   el tercer cubo se asigna al rover más cercano y el otro espera.

Esta elección prioriza la pareja más cercana; no minimiza la suma global de
recorridos. El rover que acaba primero espera al compañero antes del tercer
cubo. Se conserva la navegación existente: colocarse detrás del cubo y empujarlo
hacia su depósito. No hay pinza motorizada en la lista del kit.

Las dimensiones, coordenadas y depósitos se leen del contrato v2, sin fijarlos
en el firmware. La entrega usa la condición geométrica del contrato: cubo
completo dentro del rectángulo. No se declara entregado por cercanía del rover.

## Comunicación y parada

`comun/coordinacion.py` contiene la lógica portable; `firmware/main.py` conecta
esa lógica a `firmware/comm_espnow.py`. Se envía un estado cada 100 ms, con sesión
de arranque, contador de paquete, revisión del plan y confirmación de finalización.
Los planes se repiten: perder un paquete no pierde el encargo. El líder espera
la confirmación de revisión antes de moverse. Contadores repetidos no renuevan
el plazo del enlace. Un cambio de sesión retira el plan previo.

Sin comunicación válida durante 750 ms, los rovers frenan. No hay sustitución
automática del líder ni reparto independiente al perder la radio. También se
frena con telemetría ausente durante 500 ms, pose/cubo viejos o ausentes, y fuera
de `RUNNING`. Se conserva el paro final ante excepciones del firmware.

ESP-NOW se inicia después de conectar WiFi y usa `Peer(channel=0)`, el canal
actual de la radio. Ambos deben usar el mismo canal WiFi de 2.4 GHz; dos puntos
de acceso con el mismo SSID podrían estar en canales distintos.
Referencia: [API ESP-NOW de CircuitPython](https://docs.circuitpython.org/en/latest/shared-bindings/espnow/index.html).

## Validación y puesta en marcha

Se ejecutaron **71 pruebas**: pruebas anteriores, elección por MAC, reparto,
confirmación, caducidad, paquetes repetidos, reinicio del seguidor, datos viejos
y una simulación completa con pérdida de uno de cada cinco intercambios. En ese
escenario los tres cubos se entregan sin choques. No es una prueba física ni
garantiza evitar choques en cualquier distribución de la cancha.

El modo estático sigue disponible en `ControladorRover` para las simulaciones
anteriores; el firmware usa explícitamente `coordinado=True` y nunca recurre al
reparto estático al perder ESP-NOW.

**Desplegado en COM3 y COM4 el 1-oct-2026 por solicitud del usuario.** Se
verificaron los 19 archivos byte a byte contra la fuente local en cada placa,
y ambas importaron `firmware.main` correctamente. COM3 confirmó ArUco 10,
seguidor; COM4 ArUco 11, líder. Ambas tienen `VISION_HOST` configurado; no se
probó conexión al servidor. Se conservaron WiFi, `settings.toml` y `/lib`.
Respaldos de los archivos reemplazados en
`rover_original/antes_espnow_COM3_20261001_093846/` y
`rover_original/antes_espnow_COM4_20261001_093930/` (sin credenciales).
Las placas quedaron en REPL: reiniciar para ejecutar `code.py`.
**No se realizaron pruebas de movimiento físico.** Preparar
la IP de visión y WiFi en el `settings.toml` de cada placa, conservar el respaldo
y verificar identidad, canal, mensajes y sensores con ruedas levantadas antes
de probar en cancha. El ultrasónico y las velocidades requieren calibración;
el sensor de color no está integrado. La evitación de colisiones sigue siendo
la regla básica del proyecto; no incluye planificación de rutas entre obstáculos.

Para revisar qué se copiaría (sin escribir en los rovers):

```powershell
python herramientas/desplegar.py COM3
python herramientas/desplegar.py COM4
```

Tras acordar el despliegue con el equipo, los mismos comandos con `--si` copian
el firmware compartido. No modifican `settings.toml` ni las bibliotecas de placa.
