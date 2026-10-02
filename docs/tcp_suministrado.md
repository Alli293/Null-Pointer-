# Transporte TCP suministrado por el usuario

Integración local del 2-oct-2026. `firmware/tcp_usuario.py` es copia byte por
byte del adjunto del usuario: constantes, tiempos, búsqueda de hosts, caché,
imports y funciones sin cambios. `firmware/buffer_ndjson.py` reproduce el
buffer pegado, restaurando la indentación y los guiones bajos del formato del
mensaje, sin cambiar su lógica ni sus valores.

`config.py` en la raíz adapta los nombres WIFI_SSID/WIFI_PASSWORD a las mismas
variables CIRCUITPY_WIFI_SSID/CIRCUITPY_WIFI_PASSWORD de settings.toml. No cambia
las credenciales ni la IP. Los dos métodos de despliegue incluyen este archivo.

`firmware/comm_vision.py` es el adaptador al controlador. Usa abrir_tcp y
drenar_tcp del adjunto. Entrega cada seq una sola vez y reconecta tras 0.75 s
sin secuencia nueva, limpiando el buffer. El paro existente de motores a los
500 ms sin telemetría sigue vigente entre lecturas. El adjunto conserva su
bucle de drenaje original; los plazos dependen de que ese bucle retorne.
El enlace entre rovers continúa por ESP-NOW; TCP conecta cada rover a visión.

Validación local: 75 pruebas pasan. Incluyen el buffer, seq repetidas, limpieza
al desconectar, ejecución del firmware con sockets simulados y coordinación.
Despliegue físico en rover 1 (MAC E0:8C:FE:25:C7:48, COM3): 22 archivos
verificados, importación de firmware.main y select correctas. Respaldo en
rover_original/antes_espnow_COM3_20261002_101907. Prueba sin motores: la red
configurada Visitas devuelve "No network with that ssid". No se cambió WiFi ni
VISION_HOST (192.168.50.188); la PC está actualmente en 192.168.1.13. Placa
detenida en REPL. Pendiente conectar a una red disponible y desplegar rover 2.
