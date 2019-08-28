############
# ESP32_Step28BYJ48.py  a Micropython ESP32 module for the 28BYJ48 stepper motor
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-28
# This software is licensed under the Eclipse Public License 2.0
############
import machine
import utime

class Step28BYJ48:
	"""A class for driving a 28BYJ-48 stepper motor."""

	# Sequence of 8 phases to drive the motor. Bits are IN4 IN3 IN2 IN1
	_phases = bytearray([
  	0b1000,
		0b1100,
		0b0100,
		0b0110,
		0b0010,
		0b0011,
		0b0001,
		0b1001,
	])
	
	# Minimum milliseconds per turn (max speed is one turn in 4.096s)
	minMsPerTurn = 4096
	
	def __init__(self, pin1, pin2, pin3, pin4, timer=None):
		"""
		Initialize a stepper motor with driving pins 1 to 4 named pin1, pin2, pin3 and pin4.
		If a timer number is provided, this timer will be used, else timer 5 will be used.
		"""
		self._drive = [
			machine.Pin(pin1, machine.Pin.OUT),
			machine.Pin(pin2, machine.Pin.OUT),
			machine.Pin(pin3, machine.Pin.OUT),
			machine.Pin(pin4, machine.Pin.OUT)
		]
		if timer == None:
			timer = -1
		self.msPerTurn = Step28BYJ48.minMsPerTurn  # minimum value / max speed
		self._timer = machine.Timer(timer)
		self._callback = None
		self._remainingPhases = 0

	def setSpeed(self, msPerTurn):
		"""
		Set the rotation speed in milliseconds per turn.
		Higher values mean lower rotation speed.
		"""
		if msPerTurn < Step28BYJ48.minMsPerTurn :
			raise ValueError('Minimum ms per turn is 4096')
		self.msPerTurn = msPerTurn
	
	def _phaseFreq(self):
		"""Return the frequency of the phase changes to achieve the desired speed."""
		# 4096 phase changes are needed for a turn, the speed is in ms per turn
		return (1000 * 4096) // self.msPerTurn
	
	def _phasePeriod(self):
		"""Return the period of the phase changes to achieve the desired speed."""
		return self.msPerTurn / (1000 * 4096)
	
	def _onePhase(self):
		"""Perform one phase change of the coils."""
		if self._remainingPhases == 0 :
			self._timer.deinit()
			for i in range(4) :
				self._drive[i].value(0)
			if self._callback != None :
				self._callback(self)
				self._callback = None
			return False
		self._remainingPhases -= 1
		for i in range(4) :
			self._drive[i].value((Step28BYJ48._phases[self.phase] >> i) & 1)
		self.phase += self.step
		if self.phase > 7 :
			self.phase = 0
		if self.phase < 0 :
			self.phase = 7
		return True
	
	def _setupSteps(self, n):
		"""Setup all values to perform n steps (8n phase changes)."""
		if self._remainingPhases != 0 :
			raise ValueError('Can not start a rotation while the previous one is not finished')		
		if n == 0 :
			return
		elif n > 0:
			self.phase = 0
			self.step = 1
		else:
			self.phase = 7
			self.step = -1
			n = -n
		self._remainingPhases = 8*n  # 8 phases per step
	
	def asyncSteps(self, n, callback = None):
		"""Make n steps = n*/512 turn ≈ n*0.7° asynchronously.
		   n > 0 turns counter clockwise (positive trigonometric angle).
		   n < 0 turns clockwise (negative trigonometric angle).
		   If callback is not None, it will be called when done.
		"""
		self._setupSteps(n)
		self._callback = callback
		self._timer.init(freq = self._phaseFreq(),
		                 mode = machine.Timer.PERIODIC,
		                 callback = lambda t: self._onePhase())

	def syncSteps(self, n):
		"""Make n steps = n*/512 turn ≈ n*0.7° and return when done.
		   n > 0 turns counter clockwise (positive trigonometric angle).
		   n < 0 turns clockwise (negative trigonometric angle).
		"""
		self._setupSteps(n)
		usdelay = int(self._phasePeriod() * 1E6)
		while self._onePhase() :
			utime.sleep_us(usdelay)
