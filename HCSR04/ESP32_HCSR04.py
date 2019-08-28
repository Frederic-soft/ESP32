############
# HCSR04.py a Micropython ESP32 driver for the HCSR04 ultrasound telemeter.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-28
# This software is licensed under the Eclipse Public License 2.0
############
import machine
import utime

class HCSR04:
	"""
	Measure a distance using an HC-SR04 ultrasonic ranging module
	
	Example: usrange = HCSR04(12, 13)
	With temperature correction:
	tmp36 = TMP36(32)
	usrange = HCSR04(12, 13, tmp36)
	"""
	speed15 = 340    # 340m/s at 15°C
	refTemp = 15     # reference temperature in Celsius
	corr = 0.607     # +0.607m/s / °C
	
	
	def __init__(self, trig, echo, tmp36 = None, bme280 = None):
		"""
		Initialize an HCSR04 with the trigger input on pin number trig 
		and the echo output on pin number echo.
		The optional tmp36 is an instance of TMP36 to measure the temperature 
		in order to adjust the speed of sound.
		The optional bme280 is an instance of BME280 to measure the temperature 
		in order to adjust the speed of sound.
		"""
		self.trig = machine.Pin(trig, mode = machine.Pin.OUT)
		self.echo = machine.Pin(echo, mode = machine.Pin.IN, pull = None)
		self.tmp36 = tmp36
		self.bme280 = bme280

	def measure(self):
		"""
		Perform one measure of distance, with result in centimeters.
		"""
		self.trig.value(0)
		utime.sleep_ms(1)
		self.trig.value(1)
		utime.sleep_us(11)
		self.trig.value(0)
		elapsed = machine.time_pulse_us(self.echo, 1)
		speed = HCSR04.speed15
		temp = HCSR04.refTemp
		if self.tmp36 != None :
			temp = self.tmp36.temp() / 10
		if self.bme280 != None :
			temp = self.bme280.measure()['temp'] / 100
		speed += (temp - HCSR04.refTemp) * HCSR04.corr
		# speed m/s * elapsed E-6 s / 2 = 170 E -6 m = 170 E -4 cm
		return (speed * elapsed) * 0.5E-4
	
	def distance(self):
		"""
		Return the average of a series of 5 measures, in centimeters.
		"""
		d = 0
		for i in range(5) :
			d += self.measure()
			utime.sleep_ms(1)
		return d / 5
	
	def unlock(self):
		"""
		Unlock the device if it always returns null distances.
		Forces the 'echo' output to 0 during 100ms to unlock the module.
		"""
		self.echo.init(mode = machine.Pin.OUT)
		self.echo.value(0)
		utime.sleep_ms(100)
		self.echo.init(mode = machine.Pin.IN, pull = None)
