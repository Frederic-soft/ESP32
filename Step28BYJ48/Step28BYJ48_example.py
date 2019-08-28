############
# Step28BYJ48_example.py  example of use of the Step28BYJ48 module
#
# Connect IN1..IN4 to pins 13, 12, 14 and 27
# Connect the "-" pin to the GND pin of the ESP32 board
# Connect the "+" pin to the VIN pin of the ESP32 board
# Put the jumper on (connect the two pins on the right of the "-" and "+" pins)
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-28
# This software is licensed under the Eclipse Public License 2.0
############
"""
"""
from ESP32_Step28BYJ48 import Step28BYJ48
import utime

stepper = Step28BYJ48(13, 12, 14, 27)
stepper.setSpeed(8192)

print("Forward")
stepper.syncSteps(512)

utime.sleep_ms(1000)

print("Backward")
stepper.syncSteps(-512)

print("Forward async")
stepper.asyncSteps(512, callback=lambda t: print('Done'))

# Wait so that the callback prints its message before the program terminates
print("Waiting for stepper to finish")
utime.sleep_ms(10000)

print("Bye!")
