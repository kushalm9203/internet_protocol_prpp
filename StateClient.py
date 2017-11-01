
# This file manages the state of the client after the Handshake


import threading
import random
import socket

import Packet
import PacketTranslator
import Mersenne_Twister
import SocketManager

class State:
   """This class declares the states in which a client can be"""
   cmd = 0 # Geting commands
   send = 1 # Sending payload
   recv = 2 # Receiving payload
   switching = 3 # Switching to next port

class StateClient(object):
   """The class that manages the states of a client
    _state - client option - options of the client
    server_options - options from the server
    connection - Socket connection object"""
   def __init__(self,client_options, server_options, connection):
      self._state = State.cmd
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
      """Shutdown the current socket connection. If sending finsih doing so"""
      if send:
         connection.Send(Packet.Error().wrap().encode())
      connection.Shutdown()
      connection.Stop()

   def getState(self):
      """Get the state of this connection"""
      return self._state

   def close(self):
      """Close the givem conenction"""
      self._shutdown(self._connection)

   def _setCmdState(self):
      """Set the state of connection to command state"""
      self._state = State.cmd
      self._portcounter = 0
      self._fd.close()

   def _start_switching(self):
      """Start the switching proccess to next port"""
      self._next_port = self._server_port_generator.next()
      self._prev_state = self._state
      self._state = State.switching

   def send(self,fd,target):
      """Send what is contained in the file to the target address"""
      self._state = State.send
      self._connection.Send(Packet.Management("send",target).wrap().encode()) #Send a management packet to server to declare sending
      self._fd = fd # file description
      if not self._sendn(self._portusage):
         self._setCmdState()
         return
      self._start_switching() #Start switching ports while sending

   def _sendn(self,n):
      """Send n packets in the current port"""
      for i in range(n):
         terminate = 0
         data = self._fd.read(self._payloadsize) #REad the packet to send
         packet = Packet.Data(data=data,terminate=terminate) #Create the packet data
         if len(data) < self._payloadsize: #If this is the last packet terminate teh conenction, aftyer sending the packet.`
            packet.terminate = 1
            self._connection.Send(packet.wrap().encode())
            return False
         self._connection.Send(packet.wrap().encode()) #Else just send and move to the next packet.
      return True

   def recv(self,fd,target):
      """Receive from server"""
      self._connection.Send(Packet.Management("recv",target).wrap().encode()) #Send a Management packet to server declaring receiving mode in the client side
      self._fd = fd
      self._state = State.recv

   def _recv(self,packet,connection):
      """Receive data packets in client side and write to the file"""
      self._fd.write(packet.data)
      self._portcounter += 1 #Count ports not to exceed the max numbe rof portusage.
      if packet.terminate == 1: #If server asks to termiante connection terminate it and go into command state
         self._setCmdState()
      elif self._portcounter >= self._portusage: #If we have passed the number of packet to be sent in the port, switch to the next one.
         self._portcounter = 0
         self._start_switching()


   def _switching(self,packet,connection):
      """Switching port state"""
    #If we are skiping the packet go to next packet.
      if packet.status == "skip":
         self._next_port = self._server_port_generator.next()
      elif packet.status == "okay":
    #If status is okay
         address = self._connection.get_peer_address()
         dispatcher = self._connection.Dispatcher
         self._connection.setDispatcher(None)
         self._connection.Shutdown()
         self._connection.Stop()
         self._connection = None
         self._connection = SocketManager.SocketConnection(dispatcher)
         establishing = True
         while establishing:
            try:
               self._connection.Connect(address,self._next_port)
               establishing = False
            except Exception as e:
               establishing = True
         self._connection.Start()
         self._state = self._prev_state
         if self._prev_state == State.send:
            self._prev_state = State.switching
            if not self._sendn(self._portusage):
               self._setCmdState()
               return
            self._start_switching()
         elif self._prev_state == State.recv:
            self._prev_state = State.switching
            self._state = State.recv

   def _FullPacketReceived(self,packet,connection):
      """Receiving a full packet"""
      if isinstance(packet,Packet.Error): #If an error packet return
         self._shutdown(self._connection,False)
         return
      if self._state == State.recv: #If in a receiving state
         if not isinstance(packet,Packet.Data): #If not a packet data shutdown
            print("PACKET IS NOT THE TYPE WE WANT IT TO BE (DATA)")
            self._shutdown(self._connection)
         self._recv(packet,connection) #Receive packet if a packet data
      elif self._state == State.switching: #If in a switching state
         if not isinstance(packet,Packet.Switching): #If not a switching packet shutdown connection
            print("PACKET IS NOT THE TYPE WE WANT IT TO BE (SWITCHING)")
            self._shutdown(self._connection)
         self._switching(packet,connection) #Start establishing the packet switching proccess.
      elif self._state == State.cmd: #If in a command state print about a wrong packet
         print("WE SHOULDN'T BE RECEIVING A PACKET IN THE COMMAND STATE")
      elif self._state == State.send: #If the state is sending we should not be in the state
         print("WE SHOULDN'T BE RECEIVING A PACKET IN THE SEND STATE")
