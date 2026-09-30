from ideaboard import IdeaBoard
from time import sleep
import board
import sys

ib = IdeaBoard()

# White LED Test
ib.pixel = (255, 255, 255)
sleep(1.0)

ib.pixel = (0,0,0)
sleep(1.0)

# Rainbow Test
for j in range(5):
    for i in range(256):
        ib.arcoiris = i
        
ib.pixel = (0,0,0)
    
# Turn both motors on, stop and reverse
ib.motor_1.throttle = 1.0
sleep(2)
ib.motor_1.throttle = 0.0
sleep(0.5)
ib.motor_2.throttle = 1.0
sleep(2)
ib.motor_2.throttle = 0.0
sleep(0.5)

ib.motor_1.throttle = -1.0
sleep(2)
ib.motor_1.throttle = 0.0
sleep(0.5)
ib.motor_2.throttle = -1.0
sleep(2)
ib.motor_2.throttle = 0.0
sleep(0.5)


try:
    i2c = board.I2C()  # uses board.SCL and board.SDA
except:
    print("I2C device not connected")
    sys.exit()

while not i2c.try_lock():
    pass

try:
    while True:
        print(
            "I2C addresses found:",
            [hex(device_address) for device_address in i2c.scan()],
        )
        ib.pixel = (0,255,0)
        sleep(0.5)

finally:  # unlock the i2c bus when ctrl-c'ing out of the loop
    i2c.unlock()