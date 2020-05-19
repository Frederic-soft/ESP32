# ESP32 Micropython boot.py file
This boot.py imports the netsetup module, which reads a list of WiFi network SSIDS from a network.json file and tries to connect to each of them in order of priority.
It stops when it succeeds in connecting to a network.

If it could not connect to a WiFi network and there is a network with a negative priority in the json file, it will create a WiFi network with the given SSID and password.

If it is connected to the Internet, it will setup a timer to get the time from pool.ntp.org every hour to fix the drift of the RTC

© Frédéric Boulanger <frederic.softdev@gmail.com>  
2019-09-30 -- 2020-05-19
This software is licensed under the Eclipse Public License 2.0
