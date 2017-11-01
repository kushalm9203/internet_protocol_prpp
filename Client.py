
# Establish the Client connection. Finish handhsake with server. Maintain the connection state at any point. Send, receive or close the connection.


import socket
import select
import threading

import PacketTranslator
import PacketDispatcher
import SocketManager
import HandshakeClient
import Packet

# Client class that establishes and maintains a connection as a client.
class Client(object):
   """Handles client connection"""
   def __init__(self,address,port,minport,maxport,portusage,protocol,timeout,payload):
      self._options = Packet.HS_Options(minport,maxport,portusage,protocol,timeout,payload,key=None)
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
      dispatcher = PacketDispatcher.PacketDispatcher()
      self._handshaker = HandshakeClient.HandshakeClient(self,self._options)
      dispatcher.Start(PacketTranslator.PacketTranslator(self._handshaker))
      self._connection = SocketManager.SocketConnection(dispatcher)
      self._stateManager = None
      self._address = address
      self._port = port

   def get_state(self):
      """Get the current state of the client conenction"""
      if self._stateManager is not None:
         return self._stateManager.getState()
      else:
         return False

   def Connect(self,address=None, port=None):
      """Creates the client connection to the given server address and port"""
      if address is None:
         address ='127.0.0.1'
      if port is None:
         port = 55974
      self._connection.Connect(address,port)
      self._connection.Start()

   def Start(self):
      """Starts sending first handshake packet"""
      self._connection.Send(Packet.HS_Version(1.0).wrap().encode())


   def Stop_Connection(self):
      """Stop and close conneciton to server"""
      if self._connection is not None:
         self._connection.Shutdown()
         self._connection.Stop()

   def setStateManager(self, stateManager):
      """Sets the stateManager to establish the state of the client connection at any point."""
      self._connection = None
      self._stateManager = stateManager

   def isEstablished(self):
      """Indicates whether the connection has been established, and the handshake has been finished."""
      if self._stateManager is not None:
         return True
      return False

   def send(self,fd,target):
      """Start sending or wait for handshake to complete"""
      if self.isEstablished():
         self._stateManager.send(fd,target)
      else:
         print("Please wait for handshake to complete")

   def recv(self,fd,target):
      """Start receiving or wait for handshake to complete"""
      if self.isEstablished():
         self._stateManager.recv(fd,target)
      else:
         print("Please wait for handshake to complete")

   def close(self):
      """Closes connection if connection is established"""
      if self.isEstablished():
         self._stateManager.close()
      else:
         print("No connection established to close.")


if __name__ == '__main__':
   client = Client("tux64-14",55974,55600,55700,100,"TCP",5,16)
   client.Connect()
   client.Start()
   fd = open("client_send.txt",'r')
   client.send(fd,"server_recv.txt")
