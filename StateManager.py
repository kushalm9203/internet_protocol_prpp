
# This file manages state of the server after the Handshake



import threading
import random
import socket

import Packet
import PacketTranslator
import SocketManager
import Mersenne_Twister

class State:
   """This class declares the states in which the server can be""" 
   cmd = 0 # Getting commands
   send = 1 # Sending payload
   recv = 2 # Receiving payload
   switching = 3 # Switching to next port

class StateManager(object):
   """The class that manages the states of the server
      _state - Server option"""
      
   def __init__(self,server_options, client_options, connection, verbose):
      self._state = State.cmd
      self._talk = verbose
      self._server_port_generator = Mersenne_Twister.IntegerRangeGenerator(server_options.key,
                                                                           server_options.minport,
                                                                           server_options.maxport)
      self._client_port_generator = Mersenne_Twister.IntegerRangeGenerator(client_options.key,
                                                                           client_options.minport,
                                                                           client_options.maxport)
      self._connection = connection
      self._next_connection = None
      self._fd = None
      self._prev_state = None
      self._portusage = server_options.portusage
      self._payloadsize = server_options.payload
      self._portcounter = 0

   def _shutdown(self,connection,send=False):
      """ Shuts down and stops the connection"""
      if send:
         connection.Send(Packet.Error().wrap().encode())
      connection.Shutdown()
      connection.Stop()

   def _command(self,packet,connection):
      """Executes commands in 'command' state"""
      if packet.command == "send":
         self._state = State.recv
         self._fd = open(packet.location,'w')
      elif packet.command == "recv":
         self._state = State.send
         self._fd = open(packet.location,'r')
         self._send(connection)
      elif packet.command == "close":
         self._shutdown(self._connection)

   def _recv(self,packet,connection):
      """Manages the state of server in 'receive' mode"""
      self._fd.write(packet.data)
      self._portcounter += 1
      if packet.terminate == 1:
         self._fd.close()
         self._portcounter = 0
         self._state = State.cmd
      elif self._portcounter >= self._portusage:
         self._portcounter = 0
         if self._talk:
            print("Switching")
         self._switch(connection)
 
   def _sendn(self,n):
      """Sends N packets"""
      for i in range(n):
         terminate = 0
         data = self._fd.read(self._payloadsize)
         packet = Packet.Data(data=data,terminate=terminate)
         if len(data) < self._payloadsize:
            packet.terminate = 1
            self._connection.Send(packet.wrap().encode())
            return False
         self._connection.Send(packet.wrap().encode())
      return True

   def _send(self,connection):
      """Manages the state of server in 'send' mode"""
      while True:
         if not self._sendn(self._portusage):
            self._state = State.cmd
            self._portcounter = 0
            self._fd.close()
            return
         #send_thread = threading.Thread(target=self._send(self._portusage))
         #send_thread.start()      
         self._switch(connection)
      
   def _switch(self,connection):
      """Manages state and switches ports in 'switching' state"""
      remote_address = self._connection.get_peer_address()[0]
      next_server_port = self._server_port_generator.next()
      new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
      hostname = socket.gethostname()
      binding = True
      skipPacket = Packet.Switching("skip")
      okayPacket = Packet.Switching("okay")
      while binding:
         try:
            new_socket.bind((hostname,next_server_port))
            binding = False
         except IOError, msg:
            next_server_port = self._server_port_generator.next()
            binding = True
            self._connection.Send(skipPacket.wrap().encode())
      self._connection.Send(okayPacket.wrap().encode())
      dispatcher = self._connection.Dispatcher
      self._connection.setDispatcher(None)
      new_socket.listen(5)
      listening = True
      while listening:
         if self._talk:
            print("switch: listening on: " + str(next_server_port))
         (clientsocket, address) = new_socket.accept()
         listening = False 
         if False and address != remote_address:
            listening = True
            clientsocket.close()
            (clientsocket, address) = new_socket.accept()
      if self._talk:
         print("got client back")
      new_connection = SocketManager.SocketConnection.from_socket(clientsocket,dispatcher,self._talk)
      new_connection.Start()
      self._connection = new_connection

   def _FullPacketReceived(self,packet,connection):
      """Manages state of server when a full packet is received"""
      if isinstance(packet,Packet.Error):
         self._shutdown(self.connection,False)
         return
      if self._state == State.cmd:
         if not isinstance(packet,Packet.Management):
            if self._talk:
               print("PACKET IS NOT THE TYPE WE WANT IT TO BE (MANAGEMENT)")
            self._shutdown(self._connection)
         self._command(packet,connection)
      elif self._state == State.recv:
         if not isinstance(packet,Packet.Data):
            if self._talk:
               print("PACKET IS NOT THE TYPE WE WANT IT TO BE (DATA)")
            self._shutdown(self._connection)
         self._recv(packet,connection)

