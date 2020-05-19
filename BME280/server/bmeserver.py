############
# bmeserver.py for Micropython on ESP32
#
# This module uses an HTTP server and a Web Socket server to display the pressure, 
# temperature and relative humidity read from a BME280 sensor.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2020-05-19
# This software is licensed under the Eclipse Public License 2.0
############
from httpserver import HttpServer
from wsserver import WebSocketServer
from machine import Pin
from ESP32_BME280 import BME280

"""
A subclass of WebSocketServer that implements a protocol to get
information from a BME280 sensor
"""
class BMEserver (WebSocketServer) :
  """
  Initialize the server to listen on port 8080 (the 80 port is used by the HTTP server)
  The default address mask allows connections from anywhere. Use 127.0.0.1 if
  you want to restrict connection to the local host.
  'password' is the password that will be required by the webrepl stuff to connect to the websocket.
  'ledpin' is the number of the pin for the builtin LED.
  If 'debug' is True, a transcript of the communications with the clients will be printed
  in the console.
  """
  def __init__(self, port=8080, address="0.0.0.0", password='', ledpin=2, debug=False) :
    super().__init__(port, address, password)
    self._debug = debug
    self._altitude = 0
    self._led = Pin(ledpin, Pin.OUT)
    self._bme = BME280(Pin(22), Pin(21), 0x76)
    self._bme.normalmode(BME280.TWENTY_MS)  # One measure every 20ms
    self._bme.filtering(BME280.IIR_8)       # average measures in an 8 sample sliding window
  
  def buildStatus(self, meas) :
    return "UPDATE %d %d %d %d %d" % (self._led.value(), meas['temp'], meas['press'], meas['hum'], self._altitude)
  
  """
  Process requests from the client:
    - LED_ON requests to switch the builtin LED on
    - LED_OFF requests to switch the builtin LED off
    - STAT requests to send the status of the LED
  The only possible answer is "UPDATE X T P H", where X is the status of the LED, 
  T is the temperature in 1/100 °C, P is the pressure in Pascal, 
  H is the relative humidity in 1/100 of percent
  """
  def process_request(self, message) :
    if message is None :   # Close server
      return None
    meas = self._bme.measure()
    meas['press'] = BME280.sealevel_pressure(meas, self._altitude)
    message = message.strip().split()
    if self._debug :
      print("# Received: " + str(message))
    if message[0] == "LED_ON" :
      self._led.on()
      answer = self.buildStatus(meas)
    elif message[0] == "LED_OFF" :
      self._led.off()
      answer = self.buildStatus(meas)
    elif message[0] == "SET_ALT" :
      self._altitude = int(message[1])
      meas = self._bme.measure()
      meas['press'] = BME280.sealevel_pressure(meas, self._altitude)
      answer = self.buildStatus(meas)
    elif message[0] == "STAT" :
      answer = self.buildStatus(meas)
    else :
      answer = "UNKNOWN REQUEST: " + message
    if self._debug :
      print("# Answered: " + answer)
    return answer
  
  """
  Redefined method to install process_request as the request handler
  """
  def do_accept(self, address) :
    h = super().do_accept(address)  # Reuse the superclass behavior
    if h is None :
      if self._debug :
        print("# Rejecting connection from: ", address)
    else :            # if the connection is accepted
      if self._debug :
        print("# Accepting connection from: ", address)
      return self.process_request   #   return our request handler
  
  """
  Redefined method to print a message when a connection is closed
  """
  def close_handler(self, wsreader) :
    if self._debug :
      print("# Closing connection from", self.getClientFromReader(wsreader)[0])
    super().close_handler(wsreader)  # Reuse superclass behavior to really close the connection

"""
A subclass of HttpServer that prints not found resources
"""
class MyHttpServer(HttpServer) :
  def resourceNotFound(self, rez, stream) :
    super().resourceNotFound(rez, stream)
    print("# Ressource '" + rez + "' not found")

# A suitable index.html file should be put in /www on the ESP32 internal storage
hsrv = MyHttpServer()                # Create the HTTP server on port 80
wsrv = BMEserver(8080, debug=False)  # Create the web socket server on port 8080
print("Point your browser at:", hsrv.start())  # Start the HTTP server
print("Web socket URL:", wsrv.start())         # Start the web socket server
