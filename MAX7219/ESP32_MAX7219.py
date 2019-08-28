############
# ESP32_MAX7219.py  a Micropython ESP32 driver for the MAX7219 LED driver
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2015-06-09
# This software is licensed under the Eclipse Public License 2.0
############
import machine

class MAX7219:
	"""
	Generic interface to MAX7219 7 segment display driver.
	"""
	
	NO_DECODE = 0x00	# no decode mode value for the decode register
	CODEB = 0xFF		# code B mode value for the decode register
	
	OFF = 0x00			# display off value for the shutdown register
	ON = 0x01			# display on value for the shutdown register
	
	NOTEST = 0x00		# normal operation value for the test register
	DOTEST = 0x01		# test mode value for the test register
	
	# Address of the MAX7219 d-registers
	register = {
		# Digit value registers.
		# In NO_DECODE mode, the format is: dp a b c d e f g
		#     aa
		#   f    b
		#   f    b
		#     gg
		#   e    c
		#   e    c
		#     dd   dp
		#
		# In CODEB mode, the following is displayed according to the value of the register:
		# 0x00 : 0
		# 0x01 : 1
		# 0x02 : 2
		# 0x03 : 3
		# 0x04 : 4
		# 0x05 : 5
		# 0x06 : 6
		# 0x07 : 7
		# 0x08 : 8
		# 0x09 : 9
		# 0x0A : -
		# 0x0B : E
		# 0x0C : H
		# 0x0D : L
		# 0x0E : P
		# 0x0F : <blank>
		'digit'     : (0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08),
		# Decode register. Its value sets the decode mode (NO_DECODE or CODEB)
		'decode'    : 0x09,
		# Intensity register. Set the duty cycle from 1/32 for 0x00 to 31/32 for 0x0F
		'intensity' : 0x0A,
		# Scan limit register. Display digit 0 only for 0x00, digits 0 to 7 for 0x07
		'scanlimit' : 0x0B,
		# Shutdown register. Sets the MAX7219 display on (ON) or off (OFF)
		'shutdown'  : 0x0C,
		# Test register. Puts the MAX7219 in test mode (DOTEST) or in normal operation (NOTEST)
		'test'      : 0x0F
	}
	
	"""
	Params:
	* NSS (CS), SCK (CLK), MISO, MOSI (DIN) are the pins used by the SPI protocol.
	* baudrate is the SCK clock rate
	The MISO pin is not used because the MAX7219 is a pure slave, but this parameter is still required.
	"""
	def __init__(self, NSS, SCK, MOSI, MISO, baudrate=328125):
		self.spi_bus = machine.SPI(baudrate=baudrate,
		                           sck=machine.Pin(SCK),
		                           mosi=machine.Pin(MOSI),
		                           miso=machine.Pin(MISO))
		self.CS_pin = machine.Pin(NSS)
		self.CS_pin.init(mode = machine.Pin.OUT)
		self.buffer = bytearray(2)
	
	"""
	Turn off the MAX7219 interface
	"""
	def deinit(self):
		self.spi_bus.deinit()
		self.CS_pin.init(pyb.Pin.IN)
	
	"""
	Write data to a register of the MAX7219.
	Params:
	* register is the address of the register (1 byte)
	* data is the data to write into the register (1 byte)
	"""
	def send(self, register, data):
		self.buffer[0] = register
		self.buffer[1] = data
		self.spi_bus.write(self.buffer)
		self.CS_pin.value(1)
		self.CS_pin.value(0)
	
	"""
	Set a digit of the display.
	Params:
	* number is the number of the digit (0 = leftmost, 7 = righmost)
	* value is the value writen to the digit register. It will be interpreted according to the decode mode.
	"""
	def digit(self, number, value):
		self.send(MAX7219.register['digit'][number], value)
	
	"""
	Set the decode mode.
	Params:
	* code is either MAX7219.NO_DECODE (direct bit to segment mapping), or MAX7219.CODEB (see above)
	"""
	def decode(self, code):
		self.send(MAX7219.register['decode'], code)
	
	"""
	Set the intensity of the display.
	Params:
	* percent is the percentage of the maximum intensity. 0 will set the minimum intensity, which is 1/32 of the maximum intensity.
	"""
	def intensity(self, percent):
		self.send(MAX7219.register['intensity'], int((percent * 15)/100))
	
	"""
	Set the scan limit.
	Params:
	* dig_num is the number of digit to display (1 to 8)
	"""
	def scan(self, dig_num):
		self.send(MAX7219.register['scanlimit'], dig_num - 1)
	
	"""
	Switch to off or on mode.
	Params:
	* mode is either MAX7219.ON or MAX7219.OFF
	"""
	def switch(self, mode):
		self.send(MAX7219.register['shutdown'], mode)
	
	"""
	Switch to testing or normal operation mode.
	Params:
	* test is either MAX7219.NOTEST or MAX7219.DOTEST
	In test mode, the MAX7219 switches on all segments of all digits at maximum intensity, regardless of the register values.
	"""
	def test(self, test):
		self.send(MAX7219.register['test'], test)
	
