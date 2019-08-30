############
# boot.py for Micropython on ESP32
#
# This boot file reads a list of network SSIDs from a network.json file
# placed at the root of the ESP32 file system. this file has the following structure:
# {
#   1: {"ssid":"MyFirstNetwork", "pword":"password4net1"},
#   2: {"ssid":"My2ndNetwork", "pword":"password4net2"},
#  -1: {"ssid":"MyDefaultNetwork", "pword":"password4default"},
# }
# The positive keys are priorities. There should be only one entry with a negative key.
# This code will attempt to connect to each WiFi network, in order of priority, and
# stop as soon as a connection is successful.
#
# If no connection could be made, it will create a WiFi network with SSID and password
# according to the entry with a negative key if there is one.
#
# If it is connected to the Internet, it will setup a timer to get the time 
# from pool.ntp.org every hour and set the RTC time and date.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2019-08-30
# This software is licensed under the Eclipse Public License 2.0
############
import esp
esp.osdebug(None)
import network
import usocket
import utime
import ujson
from ntptime import settime
from machine import Timer

# Get list of known WiFi networks
try :
  with open('/networks.json', 'r') as netfile :
    knownnets = ujson.load(netfile)
except exception :
  knownnets = {}

# Sort priorities of SSIDs
netprio = list(knownnets.keys())
netprio.sort()

if len(netprio) > 0 :
  # Firstly, try to connect to a known WiFi network
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  networks = wlan.scan()
  # Get the SSIDs of the networks
  netnames = [n[0].decode('utf-8') for n in networks]
  for net in netprio : # Try networks in priority order
    if net < 0 :       # Negative priority = default network, ignore for now
      continue
    ssid = knownnets[net]['ssid']
    if ssid in netnames :
      print("Trying to connect to", ssid)
      wlan.connect(ssid, knownnets[net]['pword'])
      utime.sleep(5)  # Wait 5 seconds for the connection
      if wlan.isconnected() :
        print("Success!")
        break
      print("Failure.")

  # Secondly, if no network was found, create our own
  if not wlan.isconnected() :
    wlan.active(False)
    for net in netprio :
      if net >= 0 :  # Existing network to which we could not connect
        continue
      wlan = network.WLAN(network.AP_IF)
      wlan.active(True)
      wlan.config(essid=knownnets[net]['ssid'], password=knownnets[net]['pword'])

# Print our IP address and the network we are on
print(wlan.ifconfig()[0], " on ", wlan.config('essid'))

# If we can reach an NTP server, setup a timer to fix the drift of the RTC every hour
if len(usocket.getaddrinfo('pool.ntp.org', 123)) > 0 :
  # Setup a timer to set the time from pool.ntp.org
  ntp_timer = Timer(-1)
  ntp_timer.init(period=3600000, mode=Timer.PERIODIC, callback=lambda t:settime())
  settime()
