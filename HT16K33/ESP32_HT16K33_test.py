############
# ESP32_HT16K33_test.py
#
# Test for the ESP32_HT16K33 Micropython ESP32 driver for the 7-segment LED HT16K33 backpack.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-07
# This software is licensed under the Eclipse Public License 2.0
############
import machine
from ESP32_HT16K33 import HT16K33

def main():
  # Interface to the I2C bus with SCL on pin 4 and SDA on pin 0
  scl = machine.Pin(4)
  sda = machine.Pin(0)
  display = HT16K33(scl, sda)
  display.switch_on()
  display.count()
  display.dispString('mPython iS cool. ')
