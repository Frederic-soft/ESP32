############
# ESP32_pca9685fb.py a Micropython ESP32 driver for the PCA9685 PWM timer chip.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-30
# This software is licensed under the Eclipse Public License 2.0
############
import machine
import utime
import sys

class PCA9685:
  # PCA9685 registers
  MODE1_REG = 0     # Mode register 1
  MODE2_REG = 1     # Mode register 2
  SUBA1_REG = 2     # I2C subaddress 1
  SUBA2_REG = 3     # I2C subaddress 2
  SUBA3_REG = 4     # I2C subaddress 3
  ALLAD_REG = 5     # I2C All Call address
  ALL_ON_L  = 250   # All LEDs on time LSB
  ALL_ON_H  = 251   # All LEDs on time MSB
  ALL_OFF_L = 252   # All LEDs off time LSB
  ALL_OFF_H = 253   # All LEDs off time MSB
  
  # Individual LEDs registers 0..15, LED 16 is all LEDs """
  LED_ON_L  = tuple(range(6,67,4))+(ALL_ON_L,) # LSB of the ON counter for LEDS 0..15
  LED_ON_H  = tuple(range(7,68,4))+(ALL_ON_H,) # MSB of the ON counter for LEDS 0..15
  LED_OFF_L = tuple(range(8,69,4))+(ALL_OFF_L,) # LSB of the OFF counter for LEDS 0..15
  LED_OFF_H = tuple(range(9,70,4))+(ALL_OFF_H,) # MSB of the OFF counter for LEDS 0..15
  PRESC_REG = 254   # Prescale register
  TEST_REG  = 255   # Test mode register

  # Bits of MODE1 register
  RESTART = 0b10000000   # PCA9685 is ready to restart PWM timers
  EXTCLK  = 0b01000000   # use external clock
  AUTOINC = 0b00100000   # enable register address auto-increment
  SLEEP   = 0b00010000   # turn off internal oscillator (low power mode)
  SUBADR1 = 0b00001000   # respond to I2C subaddress 1
  SUBADR2 = 0b00000100   # respond to I2C subaddress 2
  SUBADR3 = 0b00000010   # respond to I2C subaddress 3
  ALLCALL = 0b00000001   # respond to I2C All Call address

  # Bits in MODE2 register
  INVERT  = 0b00010000   # Output logic state inverted. Use when no external driver used
  OUTCHG  = 0b00001000   # Outputs change on ACK. Else, they change on STOP, allowing sync of several PCA9685
  OUTDRV  = 0b00000100   # Totem pole LED outputs (versus open drain)
  OUTNEH  = 0b00000010   # High impedance outputs when /OE = 1
  OUTNEL  = 0b00000001   # Default ouput value when /OE = 1 and OUTNEH = 0

  # Bits in LED registers
  LED_ON  = 0b00010000   # turn LED on in LED_ON_H register
  LED_OFF = 0b00010000   # turn LED off in LED_OFF_H register (has priority over LED_ON in LED_ON_H)

  def __init__(self, scl, sda, address = 0x60):
    """
    Create a PCA9785 object on an I2C bus at a given address.
    scl is the pin number of the SCL pin
    sda is the pin number of the SDA pin
    """
    self._i2c = machine.I2C(scl=machine.Pin(scl), sda=machine.Pin(sda))
    self._address = address
    self.buf = bytearray(1) # one-byte buffer for I2C communications

  def _write(self, data, register):
    """ Write one byte in a register """
    self._i2c.writeto_mem(self._address, register, data)

  def _read(self, register):
    """ Read one byte from a register """
    return self._i2c.readfrom_mem(self._address, register, 1)

  def _setBit(self, bit, register):
    """ Set a bit to 1 in a register """
    self.buf[0] = self._read(register)[0] | bit
    self._write(self.buf, register)

  def _clearBit(self, bit, register):
    """ Clear a bit to 0 in a register """
    self.buf[0] = self._read(register)[0] & (~bit)
    self._write(self.buf, register)

  def _testBit(self, bit, register):
    """ Tells if a bit is 1 in a register """
    r = self._read(register)
    return (r[0] & bit) != 0

  def _setTwoBytes(self, value, low_reg, high_reg):
    """ Write a two byte value in a pair of registers """
    val = value.to_bytes(2, 'little')
    self.buf[0] = val[0]
    self._write(self.buf, low_reg)
    self.buf[0] = val[1]
    self._write(self.buf, high_reg)
  
  def _getTwoBytes(self, low_reg, high_reg):
    """ Read a two byte value from a pair of registers """
    l = self._read(low_reg)
    h = self._read(high_reg)
    return 256 * h[0] + l[0]
  
  def _checkLED(self, led):
    """ Check the validity of an LED number (LED 16 is all LEDs) """
    if ((led < 0) or (led > 16)):
      raise ValueError('Invalid LED index')

  def _checkLengthValue(self, length):
    """ Check the validity of a time length (4096 is ON or OFF depending on the register) """
    if ((length < 0) or (length > 4096)):
      raise ValueError('Invalid 12 bit length')
  
  def enableAllCall(self, enable = True):
    """ Enable the Call All address """
    if (enable):
      self._setBit(PCA9685.ALLCALL, PCA9685.MODE1_REG)
    else:
      self._clearBit(PCA9685.ALLCALL, PCA9685.MODE1_REG)

  def getFreq(self):
    """ Get the PWM frequency """
    prescale = self._read(PCA9685.PRESC_REG)[0]
    return 25e6/(4096*(prescale + 1.0))
      
  def setFreq(self, freq):
    """ Set the PWM frequency from 24Hz to 1526Hz """
    prescale = round(25e6 / (4096 * freq)) - 1
    if (prescale < 3):
      prescale = 3
    if (prescale > 255):
      prescale = 255
    self.sleep()
    self._write(prescale.to_bytes(1, sys.byteorder), PCA9685.PRESC_REG)
    self.restart()
      
  def start(self):
    """ Start the internal clock. """
    # Make sure everything is off
    self._setBit(PCA9685.LED_OFF, PCA9685.ALL_OFF_H)
    # Start the internal clock
    self._clearBit(PCA9685.SLEEP, PCA9685.MODE1_REG)
    # Reset the RESTART bit if is was set
    if (self._testBit(PCA9685.RESTART, PCA9685.MODE1_REG)):
      self._setBit(PCA9685.RESTART, PCA9685.MODE1_REG)

  def stop(self):
    """ Stop all PWM channels and stop the internal clock. """
    self._setBit(PCA9685.LED_OFF, PCA9685.ALL_OFF_H)
    self.sleep()

  def sleep(self):
    """
    Stop the internal clock. This will set the restart bit if all PWM
    channels are not stopped. In this case, using restart() will restore
    all PWM settings.
    """
    self._setBit(PCA9685.SLEEP, PCA9685.MODE1_REG)

  def restart(self):
    """
    Restart the internal clock, preserving all PWM settings after
    sleep has been called while some PWM channels were active.
    """
    m = self._read(PCA9685.MODE1_REG)
    if (not self._testBit(PCA9685.RESTART, PCA9685.MODE1_REG)):
      # If the RESTART bit is not set, there is nothing to do
      return
    self._clearBit(PCA9685.SLEEP, PCA9685.MODE1_REG)
    utime.sleep_ms(1)  # wait 1ms (minimum is 500µs)
    # Set bit RESTART to 1 to clear it and restart the PWM channels
    self._setBit(PCA9685.RESTART, PCA9685.MODE1_REG)

  def reset(self):
    """
    Reset the PCA9685 (in fact all PCA9685 connected to the I2C bus are reset
    by this call). See 'Software reset' in the PCA9685 documentation.
    """
    self.buf[0] = 6
    self._i2c.writeto(0x00, self.buf)
  
  def setPWM(self, led, on, off):
    """ Set the PWM on and off times for an LED """
    self._checkLED(led)
    self._checkLengthValue(on)
    self._checkLengthValue(off)
    self._setTwoBytes(on, PCA9685.LED_ON_L[led], PCA9685.LED_ON_H[led])
    self._setTwoBytes(off, PCA9685.LED_OFF_L[led], PCA9685.LED_OFF_H[led])
  
  def getPWM(self, led):
    """ Get the PWM on and off times for an LED """
    self._checkLED(led)
    on = self._getTwoBytes(PCA9685.LED_ON_L[led], PCA9685.LED_ON_H[led])
    off = self._getTwoBytes(PCA9685.LED_OFF_L[led], PCA9685.LED_OFF_H[led])
    return (on, off)
  
  def setDuty(self, led, rate):
    """
    Set the duty cycle of an LED.
    0 means off, 4096 means on.
    In between, the PWM signal will start at 0 and stop at rate
    """
    if (rate < 0):
      rate = 0
    if (rate > 4096):
      rate = 4096
    if (rate == 0):
      self.setPWM(led, 0, 4096)
    elif (rate == 4096):
      self.setPWM(led, 4096, 0)
    else:
      self.setPWM(led, 0, rate)
  
  def setDutyPct(self, led, pct):
    """
    Set the duty cycle of an LED in percents.
    0 means off, 100 means on.
    """
    rate = int(pct * 4096 / 100)
    self.setDuty(led, rate)
