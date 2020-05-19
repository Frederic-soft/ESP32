############
# wsserver.py for Micropython on ESP32
#
# This module implements a minimalistic websocket server. It reuses the websocket 
# support that is built into Micropython for the web REPL. It extracts lines
# of text from a websocket, passes each line to a callback and sends the result
# of the callback on the websocket.
#
# Basic usage:
#   - define a subclass of WebSocketServer which redefines the do_accept method.
#     This method receives the address of the client and should return:
#     * None if the connection is refused
#     * a method to process requests from the client if the connection is accepted.
#       This method will be called and passed the string sent by the client for each 
#       request, or None when the client closes the connection by sending Ctrl-C (code 3).
#       It should return a string, which is the answer to send to the client, or None
#       when nothing is to be sent back.
#   
#   See the ledserver.py example for an example of use. You may have to edit the
#   file to set the right pin number for the builtin LED on your board.
#
# © Frédéric Boulanger <frederic.softdev@gmail.com>
# 2020-05-10 -- 2020-05-19
# This software is licensed under the Eclipse Public License 2.0
############
import socket
import network
import uwebsocket
import websocket_helper
import _webrepl

"""
A class to read data from the very constrained web sockets used 
by the web REPL in MicroPython.
"""
class WSReader :
  """
  Initialize a WSReader for reading on websocket ws, used by WebSocketServer src,
  calling srv_clbck to process each line receives
  """
  def __init__(self, ws, srv, srv_clbck) :
    self._websocket = ws
    self._server = srv
    self._srv_clbck = srv_clbck
    self._buffer = bytearray(256)  # Buffer for storing read data
    self._idx = 0                  # Deposit index in the buffer
    self._last = b'0'              # Last character read (for processing \r\n)
  
  """Write a string to the socket."""
  def write(self, string) :
    self._websocket.write(string.encode())
  
  """Close the socket, call the close_handler of the web socket server."""
  def close(self) :
    self._websocket.close()
    self._server.close_handler(self)
  
  """
  Process raw data from the web socket.
  Each time a line is read, it is sent to the callback method for processing.
  Ctrl-C (ascii code 03) is interpreted as "Stop the server".
  """
  def _client_cbk(self, sock) :
    c = self._websocket.read(1)       # Web REPL web sockets can be read 1 byte at a time only
    if (c is None) :                  # Data stolen by the web REPL stuff ?
      return
    if (len(c) == 0) :                # End of stream
      self.close()
      return
    if c[0] == 3 :                    # Ctrl-C
      answer = self._srv_clbck(None)  # Call the callback with None to indicate the end of service
      if not (answer is None) :
        self.write(answer + "\r\n")
      self.close()                    # Close the socket
      return
    eol = False
    if c[0] == 10 :          # '\n': avoid counting \r\n as two EOL
      if self._last != 13 :  # if the previous character was not '\r'
        eol = True           #   this counts as an EOL
    elif c[0] == 13 :        # '\r' is always an EOL
      eol = True
    else :                   # not an EOL --> store in buffer
      self._buffer[self._idx] = c[0]
      self._idx += 1
      if self._idx == len(self._buffer) :
        eol = True           # Buffer is full, need to empty it before EOL
    self._last = c[0]        # Memorize this character as the last one read
    if eol :                 # Flush buffer = process request and send back the answer
      l = self._buffer[0:self._idx].decode() # decode the bytes into a string
      self._idx = 0                          # reset the deposit index at the start of the buffer
      answer = self._srv_clbck(l)            # process the request
      if not (answer is None) :              # if there is an answer
        self.write(answer + "\r\n")          #   send it back to the client

"""
A class for simple web socket servers
"""
class WebSocketServer :
  """
  Initialize a web socket server listening on the given port to requests
  from the given mask ("0.0.0.0" accepts requests from any address), with
  the given web REPL password.
  """
  def __init__(self, port=80, address="0.0.0.0", password='') :
    self._port = port
    self._address = address
    self._listen_sock = None
    self._clients = []   # list of pairs (address, websocketreader)
    self._password = password
  
  """
  Stop the server and close all client connections.
  """
  def stop(self) :
    if not (self._listen_sock is None) :
      self._listen_sock.close()
    for cs in self._clients :
      cs[1].close()
    self._clients = []
  
  """
  Start the server, return the URL at which it can be reached.
  """
  def start(self) :
    self.stop()
    _webrepl.password(self._password)
    self._listen_sock = socket.socket()
    self._listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self._listen_sock.bind(socket.getaddrinfo(self._address, self._port)[0][4])
    self._listen_sock.listen(1)
    # Register callback
    self._listen_sock.setsockopt(socket.SOL_SOCKET, 20, self._accept_handler)
    for i in (network.AP_IF, network.STA_IF) :
      iface = network.WLAN(i)
      if iface.active() :
        return "ws://%s:%d" % (iface.ifconfig()[0], self._port)
    return ""
  
  """
  Default behavior for processing requests. It simply sends the message back to the client.
  This should be redefined in a subclass to implement the behavior of the server.
  """
  def echo(self, message) :
    return message
  
  """
  Default behavior for accepting connections from clients.
  It accepts any connection from an address that is not already connected,
  and returns the "echo" method for handling the requests.
  This can be redefined in a subclass for choosing which connections are accepted 
  and returning another request handler.
  """
  def do_accept(self, address) :
    for cl in self._clients :
      if cl[0] == address :  # If there is already a connection from that address
        return None          #   reject the connection
    return self.echo         # Else handle the connection by echoing received data
  
  """
  Private method for handling connections from clients
  """
  def _accept_handler(self, sock) :
    (client_sock, client_addr) = sock.accept()
    callback = self.do_accept(client_addr)
    if callback is None : # connection is rejected
      client_sock.close()
      return
    # Use the web REPL socket stuff to handle the connection
    websocket_helper.server_handshake(client_sock)
    websock = uwebsocket.websocket(client_sock, True) # Blocking writes
    webreplsock = _webrepl._webrepl(websock)
    client_sock.setblocking(False)
    # Create a WSReader to read characters one by one and process lines
    websock_reader = WSReader(webreplsock, self, callback)
    # Update the list of connected clients
    self._clients.append((client_addr, websock_reader))
    # Let the WSReader callback handle incoming data
    client_sock.setsockopt(socket.SOL_SOCKET, 20, websock_reader._client_cbk)

  """
  Get the pair (client address, WSReader) that matched wsreader, or None
  """
  def getClientFromReader(self, wsreader) :
    for cl in self._clients :
      if cl[1] == wsreader :
        return cl
    return None
  
  """
  Handle closing a connection.
  Can be redefined in a subclass, but super().close_handler(wsreader) should
  be called to maintain the list of clients up to date.
  """
  def close_handler(self, wsreader) :
    cl = self.getClientFromReader(wsreader)
    if not (cl is None) :
      self._clients.remove(cl)
