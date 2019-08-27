############
# HT16K334x7.py a Micropython ESP32 driver for Adafruit 7-segment 4-digit 
#               LED display with HT16K33 backpack.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2015-08-27
# This software is licensed under the Eclipse Public License 2.0
############
import machine
import utime

class HT16K334x7:
	"""
	Driver for AdaFruit 4-digit 7-segment display with HT16K33 backpack.
	frederic.softdev@gmail.com
	© Frédéric Boulanger <frederic.softdev@gmail.com>
	2015-08-27
	"""
	
	# Address of the HT16K33 registers used for display
	register = {
	  'dispAddr' : 0x00,	# for writing to the internal RAM
	  'sysSetup' : 0x20,	# for system setup
	  'dispSetup': 0x80,	# for display setup
	  'dimming'	 : 0xE0		# for dimming the display
	}

	# Address of the digits in the internal RAM, from leftmost (0) to rightmost (3)
	digAddr = (0x0, 0x2, 0x6, 0x8)
	
	# Address of the o'clock dots between digits 1 and 2
	dotsAddr = 0x04

	dotsOn	= 0x02
	dotsOff = 0x00
	
	# Values for the system setup register
	clockOn		= 1
	clockOff	= 0

	# Values for the display setup register
	dispOn		= 1			# display on
	dispOff		= 0			# display off
	blinkOff	= 0b000		# do not blink
	blink2Hz	= 0b010		# blink at 2Hz
	blink1Hz	= 0b100		# blink at 1Hz
	blinkHalfHz = 0b110		# blink at 0.5Hz

	decimalPointOn	= 0x80	# set bit for the decimal point
	decimalPointOff = 0x00
	
	# format: dp g f e d c b a
	#
	#	 aa
	#  f	b
	#  f	b
	#	 gg
	#  e	c
	#  e	c
	#	 dd	  dp
	#
	digitTable = (
	  0b00111111, # 0
	  0b00000110, # 1
	  0b01011011, # 2
	  0b01001111, # 3
	  0b01100110, # 4
	  0b01101101, # 5
	  0b01111100, # 6
	  0b00000111, # 7
	  0b01111111, # 8
	  0b01101111, # 9
	)

	alphaTable = {
	  '0' : 0b00111111,
	  '1' : 0b00000110,
	  '2' : 0b01011011,
	  '3' : 0b01001111,
	  '4' : 0b01100110,
	  '5' : 0b01101101,
	  '6' : 0b01111100,
	  '7' : 0b00000111,
	  '8' : 0b01111111,
	  '9' : 0b01101111,
	  'A' : 0b01110111,
	  'b' : 0b01111100,
	  'C' : 0b00111001,
	  'c' : 0b01011000,
	  'd' : 0b01011110,
	  'E' : 0b01111001,
	  'F' : 0b01110001,
	  'G' : 0b00111100,
	  'H' : 0b01110110,
	  'h' : 0b01110100,
	  'I' : 0b00000110,
	  'i' : 0b00010000,
	  'J' : 0b00001110,
	  'j' : 0b00001100,
	  'L' : 0b00111000,
	  'l' : 0b00110000,
	  'n' : 0b01010100,
	  'O' : 0b00111111,
	  'o' : 0b01011100,
	  'P' : 0b01110011,
	  'q' : 0b01100111,
	  'r' : 0b01010000,
	  'S' : 0b01101101,
	  't' : 0b01111000,
	  'U' : 0b00111110,
	  'u' : 0b00011100,
	  'y' : 0b01101110,
	  '.' : 0b10000000,
	  '-' : 0b01000000,
	  '=' : 0b01001000,
	  '_' : 0b00001000,
	  ' ' : 0b00000000,
	  'm' : 0b01110010	# mu
	}
	
	hyphen = 0b01000000	 # '-'

	def __init__(self, scl, sda, addr=0x70):
		"""
		Params:
		* scl = SCL pin for the I2C bus
		* sda = SDA pin for the I2C bus
		* addr = I2C address of the display
		"""
		self.address = addr
		self.isOn = HT16K334x7.dispOff
		self.blinkMode = HT16K334x7.blinkOff
		self.offset = 0    # offset in string being displayed
		self.string = None # string being displayed
		self.length = 0    # length of string being displayed
		self.timer = None  # timer used to scroll long strings
		self.data = bytearray(2) # 2-byte buffer
		self.buf = bytearray(1)   # 1-byte buffer
		
		self.i2c = machine.I2C(scl = scl, sda = sda)
		
		self.start()
	
	def send(self, data):
		"""
		Send some data to the HT16K33 controller
		"""
		self.i2c.writeto(self.address, data)
	
	def sendbyte(self, b):
		"""
		Send a single byte to the HT16K33 controller
		"""
		self.buf[0] = b
		self.i2c.writeto(self.address, self.buf)
	
	def start(self):
		"""
		Start the internal oscillator
		"""
		self.sendbyte(HT16K334x7.register['sysSetup'] | HT16K334x7.clockOn)
	
	def stop(self):
		"""
		Stop the internal oscillator
		"""
		self.sendbyte(HT16K334x7.register['sysSetup'] | HT16K334x7.clockOff)
	
	def on(self):
		"""
		Switch the display on
		"""
		self.isOn = HT16K334x7.dispOn
		self.sendbyte(HT16K334x7.register['dispSetup'] | self.isOn | self.blinkMode)
	
	def off(self):
		"""
		Switch the display off
		"""
		self.isOn = HT16K334x7.dispOff
		self.sendbyte(HT16K334x7.register['dispSetup'] | self.isOn | self.blinkMode)
	
	def blink(self, blinkVal):
		"""
		Set the blinking mode of the display.
		Values for blinkVal:
		* blinkOff: do not blink
		* blink2Hz: blink at 2Hz
		* blink1Hz: blink at 1Hz
		* blinkHalfHz: blink at 0.5Hz
		Any other value will switch off blinking
		"""
		if not blinkVal in (HT16K334x7.blinkOff, HT16K334x7.blink2Hz, HT16K334x7.blink1Hz, HT16K334x7.blinkHalfHz):
			blinkVal = HT16K334x7.blinkOff
		self.blinkMode = blinkVal
		self.sendbyte(HT16K334x7.register['dispSetup'] | self.isOn | self.blinkMode)

	def set_brightness(self, level):
		"""
		Set the brightness of the display.
		The 'level' parameter should be between 0 and 15.
		Other values will be clipped to this range.
		"""
		if level < 0:
			level = 0
		if level > 15:
			level = 15
		self.sendbyte(HT16K334x7.register['dimming'] | level)

	def setDots(self, on):
		"""
		Switch the o'clock dots on or off.
		The 'on' parameter is a boolean value.
		"""
		self.data[0] = HT16K334x7.register['dispAddr'] | HT16K334x7.dotsAddr
		if on:
			self.data[1] = HT16K334x7.dotsOn
		else:
			self.data[1] = HT16K334x7.dotsOff
		self.send(self.data)
	
	def display(self, dig_num, raw):
		"""
		Display a pattern on digit 'dig_num'.
		The 'raw' parameter is a byte whose bits correspond to segments
		dp g f e d c b a from the most significant bit to the least significant one.
		"""
		self.data[0] = HT16K334x7.register['dispAddr'] | HT16K334x7.digAddr[dig_num]
		self.data[1] = raw
		self.send(self.data)
	
	def clear(self):
		"""
		Clear the display (switch off all segment)
		"""
		self.stopDisplayString()
		for dig in range(4):
			self.display(dig, 0x00)
		self.setDots(False)
	
	def displayDigit(self, dig_num, value):
		"""
		Display a value on digit dig_num.
		If 'value' is negative, the decimal dot will be on.
		Digits are numbered 0 to 3 from left to right
		"""
		self.stopDisplayString()
		dot = HT16K334x7.decimalPointOff
		if value < 0:
			dot = HT16K334x7.decimalPointOn
			value = -value
		if value > 9:
			self.display(dig_num, hyphen | dot)
		else:
			self.display(dig_num, HT16K334x7.digitTable[value] | dot)
	
	def displayNumber(self, value):
		"""
		Display a number.
		If 'value' is negative, the decimal dots will be on.
		If the absolute value of 'value' is larger than 9999, hyphens will be displayed
		"""
		self.stopDisplayString()
		sign = 1
		if value < 0:
			sign = -1
			value = -value
		if value > 9999:
			for dig in range(4):
				self.display(dig, HT16K334x7.hyphen)
		else:
			for dig in range(3, -1, -1):
				self.displayDigit(dig, sign * (value % 10))
				value = value // 10
	
	def rawDisplayAlpha(self, dig_num, char, dot=False):
		"""
		Display a character on digit 'dig_num'.
		The patterns of segments for the characters are in a table.
		If the character 'char' is not in the table, nothing will be displayed.
		If 'dot' is True, the decimal point will be switched on.
		"""
		if not char in HT16K334x7.alphaTable:
			self.display(dig_num, 0x00)
		else:
			dp = HT16K334x7.decimalPointOff
			if dot:
				dp = HT16K334x7.decimalPointOn
			self.display(dig_num, HT16K334x7.alphaTable[char] | dp)
	
	def displayAlpha(self, dig_num, char, dot=False):
		"""
		Display a character on digit 'dig_num' using rawDisplayAlpha.
		Stop displaying a long string.
		"""
		self.stopDisplayString()
		self.rawDisplayAlpha(dig_num, char, dot)
	
	def dispStringInterruptHandler(self, timer):
		"""
		Timer interrupt handler for scrolling long strings on the display
		"""
		self.offset = (self.offset + 1) % self.length
		for dig in range(4):
			self.rawDisplayAlpha(dig, self.string[(dig + self.offset) % self.length])
		
	def displayString(self, string, delay=300, timer=None):
		"""
		Clear the display and display a string of characters, using displayAlpha.
		If the string has less than 4 characters, it will be displayed flushed left.
		If the string has more than 4 characters, it will scroll toward the left with
		a delay of 'delay' milliseconds between each character.
		"""
		self.stopDisplayString()
		n = len(string)
		self.clear()
		if n > 4:
			self.string = string + '    '
			self.length = n + 3
			self.offset = 0
			if timer == None :
				timer = machine.Timer(-1)
			self.timer = timer
			timer.init(
			  period=delay,
			  mode = machine.Timer.PERIODIC,
			  callback = self.dispStringInterruptHandler
			)
		for dig in range(min(n, 4)):
			self.rawDisplayAlpha(dig, string[dig])

	def stopDisplayString(self):
		if self.timer != None :
			self.timer.deinit()
			self.string = None
			self.length = 0
