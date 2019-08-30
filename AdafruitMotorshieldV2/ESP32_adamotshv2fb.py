############
# ESP32_adamotshv2fb.py a Micropython ESP32 driver for Adafruit motor shield V2.
#
# Requires the ESP32_pca9685fb module for driving the PWM timer chip.
#
# Connect for instance pins D12 and D13 of the ESP32 board
# to the SDA and SCL pins on the shield (near the pass-through servo pins).
# Connect the GND and VIN pins of the ESP32 to the Gnd and 5V pins of the shield
# (on the same side as the motor power connector).
# Also connect the VIN pin of the ESP32 to the Vin pin of the shield if you do not
# use an external power supply for the motors.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-30
# This software is licensed under the Eclipse Public License 2.0
############
from ESP32_pca9685fb import PCA9685
import math    # Only needed for math.sin. Can be precomputed if math module is not available
import utime

class DCMotor:
  """
  A DC motor connected to two of the side connectors 
  labelled M1, M2, M3 and M4 on the shield.
  """
  # Channels of the PCA9685 that are driving the motor ports M1, M2, M3 and M4
  _MOTORS = (
    {'pwm':8,  'in1':10,  'in2': 9}, # Motor 1
    {'pwm':13, 'in1':11, 'in2': 12}, # Motor 2
    {'pwm':2,  'in1':4,  'in2': 3},  # Motor 3
    {'pwm':7,  'in1':5,  'in2': 6}   # Motor 4
  )

  def __init__(self, pca, motor):
    """
    Initialize a DC motor driven by PCA9685 'pca' on port 'motor'
    """
    self._pca = pca
    if (motor < 1) or (motor > 4):
      raise ValueError('Invalid motor number (1-4)')
    self._pwm = DCMotor._MOTORS[motor-1]['pwm']
    self._in1 = DCMotor._MOTORS[motor-1]['in1']
    self._in2 = DCMotor._MOTORS[motor-1]['in2']
  
  def throttle(self, th): # th is -4096..4096
    """
    Set the throttle of this motor to 'th'.
    Negative values of 'th' make the motor run in the reverse direction
    compared to positive values. The absolute value of 'th' varies from:
      0: the motor is stopped, to
      4096: the motor is at max speed.
    """
    if th > 0: # Forward
      self._pca.setDuty(self._in2, 0)
      self._pca.setDuty(self._in1, 4096)
    elif th == 0:
      self._pca.setDuty(self._in2, 0)
      self._pca.setDuty(self._in1, 0)
    else:
      self._pca.setDuty(self._in1, 0)
      self._pca.setDuty(self._in2, 4096)
      th = -th
    self._pca.setDuty(self._pwm, th)

  def brake(self):
    """
    Make the motor stop by setting the PWM to 0 while maintaining the voltage.
    This stops the motor more quickly than juste setting the throttle to 0.
    """
    self._pca.setDuty(self._in1, 4096)
    self._pca.setDuty(self._in2, 4096)
    self._pca.setDuty(self._pwm, 0)

""" Example
pca = pca9685fb.PCA9685(1)
pca.start()
m1 = DCMotor(pca, 1)
m1.throttle(2000)
"""

# Number of micro steps in one step
MICROSTEPS = 16

class Stepper:
  """
  A stepper motor: stepper 1 is plugged on motors M1 and M2, 
  stepper 2 is plugged on motors M3 and M4
  """
  # Motor ports used for each of the two possible stepper motors
  _STEPPERS = (
    {'a': DCMotor._MOTORS[0], 'b': DCMotor._MOTORS[1]}, # Stepper 1
    {'a': DCMotor._MOTORS[2], 'b': DCMotor._MOTORS[3]}  # Stepper 2
  )

  # Coil driving phases for steper motors:
  # Even phases drive only one coil.
  # Odd phases drive two coils at once.
  _PHASES = bytes([
    0b0001,
    0b0011,
    0b0010,
    0b0110,
    0b0100,
    0b1100,
    0b1000,
    0b1001  
  ])

  # Coil drive sine computed for one quadrant ([0, π/2])
  _DRIVESINE = tuple(round(4096*math.sin(i/MICROSTEPS*math.pi/2)) for i in range(MICROSTEPS+1))

  def __init__(self, pca, stepper):
    """
    Initialize stepper motor 1 or 2 ('stepper') driven by PCA9685 'pca'
    """
    self._pca = pca
    if (stepper < 1) or (stepper > 2):
      raise ValueError('Invalid stepper number (1-2)')
    self._pwma = Stepper._STEPPERS[stepper-1]['a']['pwm']
    self._ain1 = Stepper._STEPPERS[stepper-1]['a']['in1']
    self._ain2 = Stepper._STEPPERS[stepper-1]['a']['in2']
    self._pwmb = Stepper._STEPPERS[stepper-1]['b']['pwm']
    self._bin1 = Stepper._STEPPERS[stepper-1]['b']['in1']
    self._bin2 = Stepper._STEPPERS[stepper-1]['b']['in2']
    self._drive = [0,0,0,0]
    self._drive[0] = self._ain2
    self._drive[1] = self._bin1
    self._drive[2] = self._ain1
    self._drive[3] = self._bin2
    self._phase = 0
    self._currentstep = 0
    self.power()
  
  def power(self):
    """ Power the PWM lines of the driver. """
    self._pca.setDuty(self._pwma, 4096)
    self._pca.setDuty(self._pwmb, 4096)
  
  def release(self):
    """ Shut off the power on the motor. """
    self._pca.setDuty(self._pwma, 0)
    self._pca.setDuty(self._ain1, 0)
    self._pca.setDuty(self._ain2, 0)
    self._pca.setDuty(self._pwmb, 0)
    self._pca.setDuty(self._bin1, 0)
    self._pca.setDuty(self._bin2, 0)
    self._phase = 0
  
  def waveStep(self, n, delay=20):
    """
    Perform n steps in wave drive mode (one coil at a time), 
    waiting delay milliseconds between each step.
    A negative number of steps turn in the other direction.
    """
    if n == 0:
      return
    step = 1
    if n < 0:
      step = -1
      n = -n
    for i in range(n):
      # In single step mode, the phase is always even (one coil at a time)
      if self._phase % 2 != 0 :
        self._phase += step
      else:
        self._phase += 2 * step
      # Keep the phase in [0..7]
      while self._phase < 0:
        self._phase += 8
      while self._phase > 7:
        self._phase -= 8
      # Set motor drive lines.
      self._pca.setDuty(self._pwma, 4096)
      self._pca.setDuty(self._pwmb, 4096)
      for i in range(4):
        self._pca.setDuty(self._drive[i], 4096 * ((Stepper._PHASES[self._phase] >> i) & 1))
      utime.sleep_ms(delay)
    
  def fullStep(self, n, delay=10):
    """
    Perform n steps in full drive mode (two coils at a time),
    waiting delay milliseconds between each step.
    A negative number of steps turn in the other direction.
    """
    if n == 0:
      return
    step = 1
    if n < 0:
      step = -1
      n = -n
    for i in range(n):
      # In double step mode, the phase is always odd (two coils at a time)
      if self._phase % 2 == 0 :
        self._phase += step
      else:
        self._phase += 2 * step
      # Keep the phase in [0..7]
      while self._phase < 0:
        self._phase += 8
      while self._phase >= 8:
        self._phase -= 8
      # Set motor drive lines.
      self._pca.setDuty(self._pwma, 4096)
      self._pca.setDuty(self._pwmb, 4096)
      for i in range(4):
        self._pca.setDuty(self._drive[i], 4096 * ((Stepper._PHASES[self._phase] >> i) & 1))
      utime.sleep_ms(delay)
    
  def halfStep(self, n, delay=10):
    """
    Perform n steps in half-step drive mode (alternate between one and two coils at a time),
    waiting delay milliseconds between each step.
    A negative number of steps turn in the other direction.
    This takes twice as many steps as wave and full steps to perform a revolution.
    """
    if n == 0:
      return
    step = 1
    if n < 0:
      step = -1
      n = -n
    for i in range(n):
      self._phase += step
      # Keep the phase in [0..7]
      while self._phase < 0:
        self._phase += 8
      while self._phase >= 8:
        self._phase -= 8
      # Set motor drive lines.
      self._pca.setDuty(self._pwma, 4096)
      self._pca.setDuty(self._pwmb, 4096)
      for i in range(4):
        self._pca.setDuty(self._drive[i], 4096 * ((Stepper._PHASES[self._phase] >> i) & 1))
      utime.sleep_ms(delay)
    
  def microStep(self, n, delay=1):
    """
    Perform n steps in micro-step drive mode (two coils at a time with sines in quadrature),
    waiting delay milliseconds between each step.
    A negative number of steps turn in the other direction.
    This takes MICROSTEPS times as many steps as wave and full steps to perform a revolution.
    """
    if n == 0:
      return
    step = 1
    if n < 0:
      step = -1
      n = -n
    for i in range(n):
      self._phase += step
      while self._phase < 0:
        self._phase += 4 * MICROSTEPS
      while self._phase >= 4 * MICROSTEPS:
        self._phase -= 4 * MICROSTEPS
      quadrant = self._phase // MICROSTEPS
      if (quadrant % 2) == 0 :
        power_a = Stepper._DRIVESINE[(quadrant + 1) * MICROSTEPS - self._phase]
        power_b = Stepper._DRIVESINE[self._phase - (quadrant * MICROSTEPS)]
      else:
        power_a = Stepper._DRIVESINE[self._phase - (quadrant * MICROSTEPS)]
        power_b = Stepper._DRIVESINE[(quadrant + 1) * MICROSTEPS - self._phase]
      # Set motor drive lines.
      self._pca.setDuty(self._pwma, power_a)
      self._pca.setDuty(self._pwmb, power_b)
      for i in range(4):
        self._pca.setDuty(self._drive[i], 4096 * ((Stepper._PHASES[2*quadrant+1] >> i) & 1))
      utime.sleep_ms(delay)
  
""" Example
pca = PCA9685.PCA9685(1)
pca.start()
s=Stepper(pca, 1)
s.fullStep(200)
s.microStep(-200*adamotshv2fb.MICROSTEPS)
s.release()
"""

class Servo:
  """
  A servo motor connected to one of the 4 remaining PWM output of the shield.
  Works best if the frequency of the PCA9685 is about 50Hz.
  """
  def __init__(self, pca, pwm, min_us=500, max_us=2500, range=180):
    """
    Initialize a servo motor driven by PWM number 'pwm'.
      'pwm' should be 0, 1, 14 or 15.
      'min_us' and 'max_us' are the min and max duty duration in microseconds
        to get the min and max rotation positions.
      'range is the rotation range in degrees.
    """
    if not pwm in (0, 1, 14, 15):
      raise ValueError('Servos can be driven only on ports 0, 1, 14 and 15.')
    self._pca = pca
    self._pwm = pwm
    self._minus = min_us
    self._maxus = max_us
    self._range = range
    pca.setDuty(self._pwm, 0) # release the servo
    self._period = 1e6 / pca.getFreq()
    self._minduty = int(self._minus / (self._period / 4096))
    self._maxduty = int(self._maxus / (self._period / 4096))
  
  def setDutyTime(self, us):
    """ Set the duty time of the servo in microseconds. """
    self._pca.setDuty(self._pwm, int(us / (self._period / 4096)))
  
  def release(self):
    """ Release the servo (set PWM to 0). """
    self._pca.setDuty(self._pwm, 0)
  
  def position(self, degrees):
    """ Set the position of the servo in degrees. """
    self._pca.setDuty(self._pwm, int(self._minduty + (self._maxduty - self._minduty) * (degrees / self._range)))
