############
# ESP32_HT16K33.py a Micropython ESP32 driver for the 7-segment LED HT16K33 backpack.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-07
# This software is licensed under the Eclipse Public License 2.0
############
import machine
import utime

class HT16K33 :
  register = {
    'dispAddr' : 0x00,  # Display address register
    'sysSetup' : 0x20,  # System setup register
    'dispSetup': 0x80,  # Display setup register
    'dimming'  : 0xE0   # Dimming register
  }

  # Address of the digits, from leftmost (0) to rightmost (3)
  digAddr = (0x0, 0x2, 0x6, 0x8)

  # Values for the system setup register
  clockOn = 1
  clockOff = 0

  # Values for the display setup register
  dispOn = 1
  dispOff = 0
  blinkOff = 0b000
  blink2 = 0b010
  blink1 = 0b100
  blinkh = 0b110

  # format: dp g f e d c b a
  #
  #  aa
  #  f  b
  #  f  b
  #  gg
  #  e  c
  #  e  c
  #  dd   dp
  #

  # Data for displaying digits
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

  # Data for displaying alphanumerical characters
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
    'm' : 0b01110010  # mu
  }

  """
  Initialize a HT16K33 at the given address, with SCL and SDA on the given pins
  """
  def __init__(self, scl, sda, address=0x70):
    self.i2c = machine.I2C(scl=scl, sda=sda)
    self.address = address

  # Switch the controller on
  def switch_on(self):
    buf = bytearray(1)
    buf[0] = HT16K33.register['sysSetup'] | HT16K33.clockOn
    self.i2c.writeto(self.address, buf)
    buf[0] = HT16K33.register['dispSetup'] | HT16K33.dispOn
    self.i2c.writeto(self.address, buf)

  # Switch the controller off
  def switch_off(self):
    buf = bytearray(1)
    buf[0] = HT16K33.register['dispSetup'] | HT16K33.dispOff
    self.i2c.writeto(self.address, buf)
    buf[0] = HT16K33.register['sysSetup'] | HT16K33.clockOff
    self.i2c.writeto(self.address, buf)

  # Set the brighness level
  def brightness(self, level):
    if level < 0:
      level = 0
    if level > 15:
      level = 15
    buf = bytearray(1)
    buf[0] = HT16K33.register['dimming'] | level
    self.i2c.writeto(self.address, buf)

  # Make the display blink.
  # Supported frequencies are 0 (no blinking), 0.5, 1 and 2Hz
  def blink(self, freq):
    freq = round(2*freq, 0)
    if freq >= 3:
      freq = 4
    if freq < 0:
      freq = 0
    if freq == 0:
      dim = 0x0
    elif freq == 1:
      dim = 0x3
    elif freq == 2:
      dim = 0x2
    elif freq == 4:
      dim = 0x1
    buf = bytearray(1)
    buf[0] = HT16K33.register['dispSetup'] | dim
    self.i2c.writeto(self.address, buf)

  # Display a pattern of segments on a digit
  def display(self, digit, raw):
    data = bytearray(2)
    data[0] = HT16K33.register['dispAddr'] | HT16K33.digAddr[digit]
    data[1] = raw
    self.i2c.writeto(self.address, data)

  def cleardisplay(self) :
    for digit in range(4) :
      self.display(digit, 0)

  # Display a single digit value (base 10) on a digit
  # A negative value switches the decimal point on
  def displayDigit(self, digit, value):
    dot = 0
    if value < 0: # if negative, switch the decimal dot on
      value = -value
      dot = 0x80
    if value > 9:
      value = 9
    self.display(digit, HT16K33.digitTable[value] | dot)

  # Display a number on the 4 digits
  def displayNumber(self, value):
    sign = 1
    if value < 0:
      sign = -1
      value = -value
    if value > 9999:
      value = 9999
    for i in range(3, -1, -1):
      self.displayDigit(i, sign * (value % 10))
      value = value // 10

  # Display a character on a digit
  def displayAlpha(self, digit, char):
    if not char in HT16K33.alphaTable:  # no glyph => blank digit
      self.display(digit, 0x00)
    else:
      self.display(digit, HT16K33.alphaTable[char])

  # Count from -9999 to 9999 on the display
  def count(self):
    for i in range(-9999, 10000):
      self.displayNumber(i)
      utime.sleep_ms(2)

  # Display a string of characters, scrolling it toward the left if it is longer than 4 characters
  def dispString(self, string):
    offset = 0
    n = len(string)
    while True:
      for i in range(4):
        self.displayAlpha(i, string[(i + offset) % n])
      utime.sleep_ms(300)
      offset = (offset + 1) % n
