############
# Test program for the BME280.py Micropython pyboard module.
#
# The 'main()' function uses an infinite loop to display the measurements.
#
# The 'main_timer()' function illustrates the use of the 'raw_measure' and
# the 'compensation' functions to read the measurements in the service routine
# of a timer and schedule its display in the REPL.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-26
# This software is licensed under the Eclipse Public License 2.0
############
import machine
import utime
import micropython
from ESP32_BME280 import BME280

# BME280 sensor
bme = None
# 8 bute buffer for storing raw measurement data
data_buffer = None

# Common intializations
def init() :
  global bme, data_buffer
  
  data_buffer = bytearray(8)
  sda = machine.Pin(0)
  scl = machine.Pin(4)
  bme = BME280(scl, sda, 0x76)
  bme.humidity_mode(BME280.OVRSAMP_16)
  bme.temperature_mode(BME280.OVRSAMP_16)
  bme.pressure_mode(BME280.OVRSAMP_16)
  bme.normalmode(BME280.HUNDREDTWENTYFIVE_MS)
  bme.filtering(BME280.IIR_16)

# Main program with an infinite loop to display measurements
def main() :
  global bme
  
  init()
  while True :
    m = bme.measure()
    print("Temperature = ", m['temp'] / 100, " °C")
    print("Atmospheric pressure = ", m['press'] / 100, " hPa")
    # Compute the sea level pressure assuming an altitude of 80m
    qnh = BME280.sealevel_pressure(m, 80)
    print("Seal level pressure = ", qnh / 100, " hPa")
    # Compute the altitude (should be 80m) given the sea level pressure
    print("Altitude = ", BME280.altitude(m, qnh), "m")
    print("Relative humidity = ", m['hum'] / 100, " %")
    utime.sleep_ms(1500)
    print()

# Function to print the measurements that have been recorded
# in an interrupt service routine
def print_measures(buffer) :
  global bme
  
  m = bme.compensation(buffer)
  print("Temperature = ", m['temp'] / 100, " °C")
  print("Atmospheric pressure = ", m['press'] / 100, " hPa")
  print("Relative humidity = ", m['hum'] / 100, " %")

# Interrupt service routine of our timer
# No memory allocation can be performed here, so we just get the raw
# data and store it in a preallocated buffer. Then we schedule the
# 'print_measures' function to be called as soon as possible in a
# normal context where memory can be allocated.
def timer_isr(t) :
  bme.raw_measure(data_buffer)
  micropython.schedule(print_measures, data_buffer)

# Main program which sets up a timer to trigger a measurement
# every 1.5 second and display the results
def main_timer() :
  init()
  timer = machine.Timer(-1)
  timer.init(mode=machine.Timer.PERIODIC, period=1500, callback=timer_isr)

print("Either call 'main()' or 'main_timer()' to test the module")
