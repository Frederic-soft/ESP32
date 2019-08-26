############
# ESP32_BME280.py a Micropython ESP32 driver for Bosch BME280 combined humidity, 
# pressure and temperature sensor.
# This code makes use of the compensation algorithms described in the data sheet
# available at: https://www.mouser.fr/datasheet/2/783/BST-BME280-DS002-1509607.pdf
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-26
# This software is licensed under the Eclipse Public License 2.0
############
import machine
import sys

class BME280 :
  # Adresses of the different registers of the BME280
  DIG_T1 = 0x88  # 0x88 (LSB) and 0x89 (MSB) of compensation param T1
  DIG_T2 = 0x8A  # 0x8A (LSB) and 0x8B (MSB) of compensation param T2
  DIG_T3 = 0x8C  # 0x8C (LSB) and 0x8D (MSB) of compensation param T3
  DIG_P1 = 0x8E  # 0x8E (LSB) and 0x8F (MSB) of compensation param P1
  DIG_P2 = 0x90  # 0x90 (LSB) and 0x91 (MSB) of compensation param P2
  DIG_P3 = 0x92  # 0x92 (LSB) and 0x93 (MSB) of compensation param P3
  DIG_P4 = 0x94  # 0x94 (LSB) and 0x95 (MSB) of compensation param P4
  DIG_P5 = 0x96  # 0x96 (LSB) and 0x97 (MSB) of compensation param P5
  DIG_P6 = 0x98  # 0x98 (LSB) and 0x99 (MSB) of compensation param P6
  DIG_P7 = 0x9A  # 0x9A (LSB) and 0x9B (MSB) of compensation param P7
  DIG_P8 = 0x9C  # 0x9C (LSB) and 0x9D (MSB) of compensation param P8
  DIG_P9 = 0x9E  # 0x9E (LSB) and 0x9F (MSB) of compensation param P9
  DIG_H1 = 0xA1  # 0xA1 compensation param H1
  DIG_H2 = 0xE1  # 0xE1 (LSB) and 0xE2 (MSB) of compensation param H2
  DIG_H3 = 0xE3  # 0xE3 compensation param H3
  DIG_H4 = 0xE4  # 0xE4 (MSB) and 0xE5 (3 LS bits) of compensation param H4
  DIG_H5 = 0xE5  # 0xE5 (LSB) and 0xE6 (MSB) of compensation param H5
  DIG_H6 = 0xE7  # 0xE7 compensation param H6
  
  ID_REG = 0xD0         # ID of the chip
  RST_REG = 0xE0        # Write 0xB6 to reset the sensor
  HUM_CTRL_REG = 0xF2   # Oversampling of humidity data
  STAT_REG = 0xF3       # Status register
  MEAS_REG = 0xF4       # Measure control register
  CONF_REG = 0xF5       # Configuration of the measures
  PRESS_REG = 0xF7      # 0xF7 to 0xF9: pressure MSB to LSB
  TEMP_REG = 0xFA       # 0xFA to 0xFC: temperature MSB to LSB
  HUM_REG = 0xFD        # 0xFD to 0xFE: humidity MSB and LSB

  # Status register contents
  MEASURING = 0b1000
  UPDATING  = 0b0001
  
  # Measuring and oversampling
  SKIP = 0b000
  OVRSAMP_1 = 0b001
  OVRSAMP_2 = 0b010
  OVRSAMP_4 = 0b011
  OVRSAMP_8 = 0b100
  OVRSAMP_16 = 0b101
  
  # Measuring and oversampling of temperature and pressure
  TEMP_CTRL = 5  # bits 5, 6 and 7 of the MEAS_REG register
  PRESS_CTRL = 2 # bits 2, 3 and 4 of the MEAS_REG register
  SENS_MODE = 0  # bits 0 and 1 of the MEAS_REG register
  
  HUM_MASK = 0b00000111
  # Modes fror MEAS_REG register
  TEMP_MASK = 0b11100000
  PRESS_MASK = 0b00011100
  MODE_MASK = 0b00000011
  SLEEP_MODE = 0b00
  FORCED_MODE = 0b01
  NORMAL_MODE = 0b11
  
  # Configuration
  STDBY_MASK = 0b11100000
  STDBY_TIME = 5    # bits 5, 6 and 7 of CONF_REG
  IIR_MASK = 0b00011100
  IIR_FILT = 2      # bits 2, 3 and 4 of CONF_REG
  
  # Standby times (bits 5, 6 and 7 of CONF_REG)
  HALF_MS = 0b000
  SIXTYTWODOTFIVE_MS = 0b001
  HUNDREDTWENTYFIVE_MS = 0b010
  TWOHUNDREDSFIFTY_MS = 0b011
  FIVEHUNDREDS_MS = 0b100
  THOUSAND_MS = 0b101
  TEN_MS = 0b110
  TWENTY_MS = 0b111
  
  # IIR filter settings
  IIR_OFF = 0b000    # No filtering
  IIR_2 = 0b001      # Average on a sliding window of 2 samples
  IIR_4 = 0b010      # Average on a sliding window of 4 samples
  IIR_8 = 0b011      # Average on a sliding window of 8 samples
  IIR_16 = 0b100     # Average on a sliding window of 16 samples
  
  """
  Convert bytes into an integer according to endianness ("little" or "big")
  and signedness
  """
  @staticmethod
  def int_from_bytes(b, endian = sys.byteorder, signed=False) :
    value = int.from_bytes(b, endian)
    if not signed :
      return value
    width = len(b) * 8
    if value > (1 << (width - 1)) -1 :
      value -= (1 << width)
    return value
  
  """
  Initialize a BME280 sensor on I2C bus with the given SCL and SDA pins,
  at the given address on the I2C bus.
  """
  def __init__(self, scl, sda, address = 0x76) :
    self.i2c = machine.I2C(scl=scl, sda=sda)
    self.addr = address
    try :
      self.id = BME280.int_from_bytes(self.i2c.readfrom_mem(self.addr, self.ID_REG, 1))
    except OSError :
      raise ValueError('No BME280 device on I2C bus at address ' + str(self.addr))
    if self.id != 0x60 :
      raise ValueError('I2C device at address ' + str(self.addr) + ' is not a BME280')
    
    buf = bytearray(2)
    
    # Read the compensation parameters
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_T1, buf)
    self.dig_T1 = BME280.int_from_bytes(buf, "little")
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_T2, buf)
    self.dig_T2 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_T3, buf)
    self.dig_T3 = BME280.int_from_bytes(buf, "little", signed = True)
    
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P1, buf)
    self.dig_P1 = BME280.int_from_bytes(buf, "little")
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P2, buf)
    self.dig_P2 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P3, buf)
    self.dig_P3 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P4, buf)
    self.dig_P4 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P5, buf)
    self.dig_P5 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P6, buf)
    self.dig_P6 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P7, buf)
    self.dig_P7 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P8, buf)
    self.dig_P8 = BME280.int_from_bytes(buf, "little", signed = True)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_P9, buf)
    self.dig_P9 = BME280.int_from_bytes(buf, "little", signed = True)
    
    self.dig_H1 = BME280.int_from_bytes(self.i2c.readfrom_mem(self.addr, BME280.DIG_H1, 1), "little")
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_H2, buf)
    self.dig_H2 = BME280.int_from_bytes(buf, "little", signed = True)
    self.dig_H3 = BME280.int_from_bytes(self.i2c.readfrom_mem(self.addr, BME280.DIG_H3, 1), "little")
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_H4, buf)
    self.dig_H4 = (buf[0] << 4) | (buf[1] & 0b1111)
    self.i2c.readfrom_mem_into(self.addr, BME280.DIG_H5, buf)
    self.dig_H5 = (buf[1] << 4) | ((buf[0] >> 4) & 0b1111)
    self.dig_H6 = BME280.int_from_bytes(self.i2c.readfrom_mem(self.addr, BME280.DIG_H6, 1), "little", signed = True)
    
    # Set humidity measurements with no oversampling
    buf = bytearray(1)
    buf[0] = BME280.OVRSAMP_1
    self.i2c.writeto_mem(self.addr, BME280.HUM_CTRL_REG, buf)
    # Set temperature and pressure measurements with no oversampling
    self.i2c.readfrom_mem_into(self.addr, BME280.MEAS_REG, buf)
    buf[0] &= ~(BME280.TEMP_MASK | BME280.PRESS_MASK)
    buf[0] |= (BME280.OVRSAMP_1 << BME280.TEMP_CTRL) \
            | (BME280.OVRSAMP_1 << BME280.PRESS_CTRL)
    self.i2c.writeto_mem(self.addr, BME280.MEAS_REG, buf)

  """
  Put the BME280 sensor in sleep mode (no measurement)
  """
  def sleepmode(self) :
    buf = bytearray(1)
    self.i2c.readfrom_mem_into(self.addr, BME280.MEAS_REG, buf)
    buf[0] &= ~BME280.MODE_MASK
    buf[0] |= BME280.SLEEP_MODE
    self.i2c.writeto_mem(self.addr, BME280.MEAS_REG, buf)
  
  """
  Make one measurement and go back to sleep mode
  """
  def oneshot(self) :
    buf = bytearray(1)
    self.i2c.readfrom_mem_into(self.addr, BME280.MEAS_REG, buf)
    buf[0] &= ~BME280.MODE_MASK
    buf[0] |= BME280.FORCED_MODE
    self.i2c.writeto_mem(self.addr, BME280.MEAS_REG, buf)
    # Wait for measurement to finish and for registers to be updated
    while (self.i2c.readfrom_mem(self.addr, BME280.STAT_REG, 1)[0]
        & (BME280.MEASURING | BME280.UPDATING)) != 0 :
    	pyb.delay(5)
  
  """
  Put the BME280 sensor in normal mode, with periodic measurements 
  separated by the standby duration (default is 0.5ms)
  """
  def normalmode(self, standby = 0) :
    buf = bytearray(1)
    self.i2c.readfrom_mem_into(self.addr, BME280.MEAS_REG, buf)
    buf[0] &= ~BME280.MODE_MASK
    buf[0] |= BME280.NORMAL_MODE
    self.i2c.writeto_mem(self.addr, BME280.MEAS_REG, buf)
    if standby < 0 or standby > BME280.TWENTY_MS :
    	standby = BME280.HALF_MS
    self.i2c.readfrom_mem_into(self.addr, BME280.CONF_REG, buf)
    buf[0] &= ~BME280.STDBY_MASK
    buf[0] |= (standby << BME280.STDBY_TIME)
    self.i2c.writeto_mem(self.addr, BME280.MEAS_REG, buf)
    
  """
  Configure the IIR filter.
  The IIR filter can be switched off (IIR_OFF) or it can compute an average value on a 
  sliding window of 2, 4, 8 or 16 samples (IIR_2, IIR_4, IIR_8 and IIR_16)
  """
  def filtering(self, coef) :
    if not coef in [BME280.IIR_OFF, BME280.IIR_2, BME280.IIR_4, BME280.IIR_8, BME280.IIR_16] :
      raise ValueException("IIR coefficient " + str(coef) + " is invalid")
    buf = bytearray(1)
    self.i2c.readfrom_mem_into(self.addr, BME280.CONF_REG, buf)
    buf[0] &= ~BME280.IIR_MASK
    buf[0] |= (coef << BME280.IIR_FILT)
    self.i2c.writeto_mem(self.addr, BME280.CONF_REG, buf)
  
  """
  Set the humidity measurement mode.
  The measurement can be skipped (SKIP) or performed with no oversampling (OVRSAMP_1),
  with oversampling twice (OVRSAMP_2), 4 times (OVRSAMP_4), 8 times (OVRSAMP_8) 
  or 16 times (OVRSAMP_16)
  """
  def humidity_mode(self, mode) :
    if not mode in [BME280.SKIP, BME280.OVRSAMP_1, BME280.OVRSAMP_2, BME280.OVRSAMP_4, BME280.OVRSAMP_8, BME280.OVRSAMP_16] :
      raise ValueException("Mode " + str(mode) + " is invalid")
    buf = bytearray(1)
    self.i2c.readfrom_mem_into(self.addr, BME280.HUM_CTRL_REG, buf)
    buf[0] &= ~BME280.HUM_MASK
    buf[0] |= mode
    self.i2c.writeto_mem(self.addr, BME280.HUM_CTRL_REG, buf)
    
  """
  Set the temperature measurement mode.
  The measurement can be skipped (SKIP) or performed with no oversampling (OVRSAMP_1),
  with oversampling twice (OVRSAMP_2), 4 times (OVRSAMP_4), 8 times (OVRSAMP_8) 
  or 16 times (OVRSAMP_16).
  Skipping the measurement of temperature may lead to incorrect results because the
  temperature is used in the compensation computations for the pressure and humidity.
  """
  def temperature_mode(self, mode) :
    if not mode in [BME280.SKIP, BME280.OVRSAMP_1, BME280.OVRSAMP_2, BME280.OVRSAMP_4, BME280.OVRSAMP_8, BME280.OVRSAMP_16] :
      raise ValueException("Mode " + str(mode) + " is invalid")
    buf = bytearray(1)
    self.i2c.readfrom_mem_into(self.addr, BME280.MEAS_REG, buf)
    buf[0] &= ~BME280.TEMP_MASK
    buf[0] |= (mode << BME280.TEMP_CTRL)
    self.i2c.writeto_mem(self.addr, BME280.MEAS_REG, buf)
    
  """
  Set the pressure measurement mode
  The measurement can be skipped (SKIP) or performed with no oversampling (OVRSAMP_1),
  with oversampling twice (OVRSAMP_2), 4 times (OVRSAMP_4), 8 times (OVRSAMP_8) 
  or 16 times (OVRSAMP_16)
  """
  def pressure_mode(self, mode) :
    if not mode in [BME280.SKIP, BME280.OVRSAMP_1, BME280.OVRSAMP_2, BME280.OVRSAMP_4, BME280.OVRSAMP_8, BME280.OVRSAMP_16] :
      raise ValueException("Mode " + str(mode) + " is invalid")
    buf = bytearray(1)
    self.i2c.readfrom_mem_into(self.addr, BME280.MEAS_REG, buf)
    buf[0] &= ~BME280.PRESS_MASK
    buf[0] |= (mode << BME280.PRESS_CTRL)
    self.i2c.writeto_mem(self.addr, BME280.MEAS_REG, buf)
  
  """
  Get the raw ADC values from the last measurement in an 8 bytes buffer.
  'buf' should be a bytearray of size at least 8
  This method can be called in a ISR because is does not allocate memory.
  """
  def raw_measure(self, buf) :
    self.i2c.readfrom_mem_into(self.addr, self.PRESS_REG, buf) # Read pressure, temperature and humidity all at once
    return buf
  
  """
  Compensation computation for getting the temperature, the pressure and humidity
  from the raw ADC data from the sensors.
  'buf' should be a bytearray or bytes of size at least 8
  'results' should be a dictionnary into which the results will be stored, or None, 
  in which case a new dictionnary will be created.
  The temperature ('temp' item of the dictionnary) is in 1/100 of °C
  The pressure ('press' item of the dictionnary) is pascal
  The relative humidity ('hum' item of the dictionnary) is in 1/100 of percent
  """
  def compensation(self, buf, results = None) :
    if results == None :
      results = {}
    
    press = (buf[0] << 16 | buf[1] << 8 | buf[2]) >> 4
    temp = (buf[3] << 16 | buf[4] << 8 | buf[5]) >> 4
    hum = buf[6] << 8 | buf[7]
    
    # Compensation formulas from Bosch Sensortec BME280 data sheet
    v1 = (((temp >> 3) - (self.dig_T1 << 1)) * (self.dig_T2)) >> 11
    v2 = (temp >> 4) - self.dig_T1
    v2 = (((v2 * v2) >> 12) * self.dig_T3) >> 14
    t_fine = v1 + v2
    
    temp = (t_fine * 5 + 128) >> 8 # value in hundredth of degree Celcius
    
    v1 = t_fine - 128000
    v2 = v1 * v1 * self.dig_P6
    v2 += (v1 * self.dig_P5) << 17
    v2 += (self.dig_P4 << 35)
    v1 = ((v1 * v1 * self.dig_P3) >> 8) + ((v1 * self.dig_P2) << 12)
    v1 = (((1 << 47) + v1) * self.dig_P1) >> 33
    if v1 == 0 :
      p = 0 # avoid exception caused by division by 0
    else :
      p = 1048576 - press
      p = (((p << 31) - v2) * 3125) // v1
      v1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
      v2 = (self.dig_P8 * p) >> 19
      p = ((p + v1 + v2) >> 8) + (self.dig_P7 << 4) # Pressure in Pa with 24 bits of integer part and 8 bits of fractional part
      p //= 256 # value in pascal rounded to an integer
    
    h = t_fine - 76800
    h = (((hum << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h) + 16384) >> 15) \
      * (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) * self.dig_H2 + 8192) >> 14)
    h -= (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
    if h < 0 :
      h = 0
    if h > 419430400 :
      h = 419430400
    h >>= 12   # Relative humidity with 22 bits of integer part and 10 bits of fractional part
    h *= 100
    h //= 1024 # Relative humidity in hundredth of percent
      
    results['temp'] = temp
    results['press'] = p
    results['hum'] = h
    return results
  
  """
  Get the values from the last measurement.
  The temperature ('temp' item of the dictionnary) is in 1/100 of °C
  The pressure ('press' item of the dictionnary) is pascal
  The relative humidity ('hum' item of the dictionnary) is in 1/100 of percent
  """
  def measure(self) :
    buf = bytearray(8)
    self.raw_measure(buf)
    return self.compensation(buf)
  
  """
  Compute the sea level pressure given a measurement and the current altitude in meters.
  See https://en.wikipedia.org/wiki/Barometric_formula for the formula
  """
  @staticmethod
  def sealevel_pressure(measurements, altitude) :
    T = measurements['temp'] / 100
    P = measurements['press']
    
    return ((1 + (altitude * 0.0065) / (T + 273.15)) ** 5.256) * P

  """
  Compute the altitude in meters given a measurement and the sea level pressure in Pa.
  See https://en.wikipedia.org/wiki/Barometric_formula for the formula
  """
  @staticmethod
  def altitude(measurements, sealevel_press) :
    T = measurements['temp'] / 100
    P = measurements['press']
    
    return (((sealevel_press / P) ** (1 / 5.256) -1) * (T + 273.15)) / 0.0065
