############
# HT16K334x7_test.py
# Test/demo file for the HT16K334x7 module
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2015-08-27
# This software is licensed under the Eclipse Public License 2.0
############
from ESP32_HT16K334x7 import HT16K334x7
import machine
import utime

def main() :
  # HT16K334x7 at address 0x70 on I2C bus with SCL on pin 4 and SDA on in 0
  sda = machine.Pin(0)
  scl = machine.Pin(4)
  disp = HT16K334x7(scl, sda, addr = 0x70)
  disp.on()

  disp.displayNumber(1234)
  utime.sleep_ms(1000)

  disp.displayString('cool')

  disp.set_brightness(15)
  for level in range(15,-1,-1):
    disp.set_brightness(level)
    utime.sleep_ms(200)

  for level in range(15):
    disp.set_brightness(level)
    utime.sleep_ms(200)
  disp.clear()

  snake = (
    0b00000001,
    0b10000010,
    0b01000000,
    0b10010000,
    0b00001000,
    0b10000100,
    0b01000000,
    0b10100000
  )
  sl = len(snake)
  for i in range(100):
    for d in range(4):
      disp.display(d, snake[(i + d) % sl])
    utime.sleep_ms(50)
  disp.clear()

  disp.displayDigit(0,4)
  utime.sleep_ms(500)
  disp.displayDigit(1,3)
  utime.sleep_ms(500)
  disp.displayDigit(2,2)
  utime.sleep_ms(500)
  disp.displayDigit(3,1)
  utime.sleep_ms(500)

  for i in range(10000):
    disp.displayNumber(i)
    utime.sleep_ms(3)

  disp.setDots(True)

  for i in range(4):
    disp.display(i, 0xFF)

  disp.blink(HT16K334x7.blink2Hz)
  utime.sleep_ms(2000)

  disp.displayString('mPython = cool StuFF')

  disp.blink(HT16K334x7.blinkOff)

main()
