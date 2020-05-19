############
# httpserver.py for Micropython on ESP32
#
# This module implements a minimalistic http server.
#
# It is not designed to be a full-fleged server, its purpose is
# to serve HTML files for interfacing with software that runs on the ESP32.
#
# Basic usage:
#   - put the html files in /www on the ESP32
#   - put this file in / on the ESP32
#   - setup the network for the ESP32
#   - from httpserver import HttpServer
#     srv = HttpServer()
#     srv.start()
#   - then point a browser to the url given by start()
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2020-05-10 -- 2020-05-19
# This software is licensed under the Eclipse Public License 2.0
############
import socket
import network

"""
A class for making HTTP 1.0 servers.
The default is to serve request on port 80 from any host.
Only GET requests are processed, and resources are looked up in the /www directory.
The default resource is /index.html
"""
class HttpServer :
  """
  Initialize a server for listening to requests on the given port,
  serving files from the given root directory, and sending default when / is requested.
  """
  def __init__(self, port=80, root='/www', default="/index.html") :
    self._port = port
    self._root = root
    self._default = default
    self._listen_sock = None

  """Stop the server."""
  def stop(self) :
    if not (self._listen_sock is None) :
      self._listen_sock.close()
  
  """Start the server. Return the URL at which it can be found."""
  def start(self) :
    self._listen_sock = socket.socket()
    self._listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self._listen_sock.bind(socket.getaddrinfo("0.0.0.0", self._port)[0][4])
    self._listen_sock.listen(1)
    # Register callback
    self._listen_sock.setsockopt(socket.SOL_SOCKET, 20, self._process_request)
    for i in (network.AP_IF, network.STA_IF) :
      iface = network.WLAN(i)
      if iface.active() :
        return "http://%s:%d" % (iface.ifconfig()[0], self._port)
    return ""
  
  """
  Handle a 'resource not found' error.
  rez is the path to the resource.
  stream is the client stream.
  This method may be redefined in a subclass to handle this kind of error.
  """
  def resourceNotFound(self, rez, stream) :
    stream.write("HTTP/1.0 404 Not Found\r\n\r\n".encode())
  
  """Private method for handling requests."""
  def _process_request(self, sock) :
    (client_sock, client_addr) = sock.accept()
    client_stream = client_sock.makefile("rwb")
    
    req = client_stream.readline().decode().strip()
    sreq = req.split()
    while len(req) > 0 :
      req = client_stream.readline().decode().strip()
    
    if len(sreq) > 0 :
      if sreq[0] == "GET" :
        if sreq[1]  == '/' :
          sreq[1] = self._default
        try :
          with open(self._root + sreq[1]) as rez :
            client_stream.write("HTTP/1.0 200 OK\r\n\r\n".encode())
            l = rez.readline()
            while len(l) > 0 :
              client_stream.write(l)
              l = rez.readline()
        except :
          self.resourceNotFound(sreq[1], client_stream)
      
    client_stream.close()
