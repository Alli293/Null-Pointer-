import board, neopixel, time

pixel_color = neopixel.NeoPixel(board.IO33, 1, brightness=1, auto_write=True)

for nombre, color in (("Paso 1 (debería ser ROJO)", (255,0,0)),
                      ("Paso 2 (debería ser VERDE)", (0,255,0)),
                      ("Paso 3 (debería ser AZUL)", (0,0,255))):
    print(nombre)
    pixel_color[0] = color
    time.sleep(3)

pixel_color[0] = (0,0,0)