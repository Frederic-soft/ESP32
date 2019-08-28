############
# HCSR04_test.py test/demo of the HCSR04 module
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-28
# This software is licensed under the Eclipse Public License 2.0
############
from ESP32_HCSR04 import HCSR04
import utime

def main() :
  telemeter = HCSR04(12, 13)
  
  while True :
    print('D:', telemeter.measure(), 'cm')
    utime.sleep_ms(500)

def main_tmp() :
  from ESP32_TMP36 import TMP36
  
  tmp = TMP36(32)
  telemeter = HCSR04(12, 13, tmp36 = tmp)
  
  while True :
    print('D:', telemeter.measure(), 'cm')
    print('T:', tmp.measure()/10, '°C')
    utime.sleep_ms(500)

def main_bme() :
  from ESP32_BME280 import BME280
  
  bme = BME280(1)
  bme.normalmode()
  telemeter = HCSR04(12, 13, bme280 = bme)
  
  while True :
    print('D:', telemeter.measure(), 'cm')
    print('T:', bme.measure()['temp']/100, '°C')
    utime.sleep_ms(500)

# Try one of these according to the temperature sensor you have
main()
#main_bme()
#main_tmp()
