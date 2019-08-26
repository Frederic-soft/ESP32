############
# bmedisplay.py
# A simple weather station that displays the temperature, the pressure and the humidity
# read from a BME280 sensor onto a 7-segment 4 digit display with HT16K33 backpack/
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-26
# This software is licensed under the Eclipse Public License 2.0
############
from ESP32_BME280 import BME280
from ESP32_HT16K33 import HT16K33
import machine
import utime

def main() :
  sda = machine.Pin(0)
  scl = machine.Pin(4)
  bme = BME280(scl, sda, 0x76)
  display = HT16K33(scl, sda, 0x70)
  
  bme.normalmode()
  bme.filtering(BME280.IIR_8)
  bme.humidity_mode(BME280.OVRSAMP_4)
  bme.pressure_mode(BME280.OVRSAMP_4)
  bme.temperature_mode(BME280.OVRSAMP_4)

  display.switch_on()
  # Clear all digits
  display.cleardisplay()
  
  while True:
    m = bme.measure()
    display.displayNumber(m['temp'])
    utime.sleep_ms(1000)
    display.displayNumber(m['press']//100)
    utime.sleep_ms(1000)
    display.displayNumber(m['hum'])
    utime.sleep_ms(1000)
    display.cleardisplay()
    utime.sleep_ms(1500)
    