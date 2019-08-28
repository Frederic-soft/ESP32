############
# LEDMatrixExample.py  Example/demo of the LEDMatrixWithMax module
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-28
# This software is licensed under the Eclipse Public License 2.0
############
import utime
from ESP32_LEDMatrixWithMAX import *

m = LEDMatrixWithMAX(NSS=27, SCK=14, MOSI=13, MISO=12)
m.on()
m.clearDisplay()
for i in range(8):
    m.setPixel(i,i,True)
m.updateDisplay()

intensity = 100
step = -1
for _ in range(500) :
  m.setIntensity(intensity)
  utime.sleep_ms(10)
  intensity += step
  if intensity == 0:
    step = 1
  if intensity == 100:
    step = -1

while True :
  for k in range(8) :
    m.clearDisplay()
    for i in range(k+1) :
      m.setPixel(i, k-i, True)
    m.updateDisplay()
    utime.sleep_ms(100)
  for k in range(7) :
    m.clearDisplay()
    for i in range(k,7) :
      m.setPixel(7+k-i, i+1, True)
    m.updateDisplay()
    utime.sleep_ms(100)
