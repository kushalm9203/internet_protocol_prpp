
# This file handles the handshake for the server - Checks if the protocols on the server and the client are compatible and if successful gets the server ready for data trasfer.

import random

import Packet
import PacketTranslator
import Mersenne_Twister
import StateManager

def randint():
   """ Returns a random number using the Mersenne_Twister"""
   rand = random.random()
   return int(rand*Mersenne_Twister.MT_RAND_MAX)

class HandshakeManager(object):
   """Manages the initial "handshake" """ 
   def __init__(self,minport=43124,maxport=44320,verbose=False):
      self._state = 0
      self._minport=minport
      self._maxport=maxport
      self._talk=verbose

   def _shutdown(self,connection,send=False):
      """Shuts down the connection"""
      if send:
         connection.Send(Packet.Error().wrap().encode())
      connection.Shutdown()
      connection.Stop()

   def _FullPacketReceived(self,packet,connection):
      """Decides if the 'protocol', 'version', packet types of the client and the server are in agreement"""
      if isinstance(packet,Packet.Error):
         self._shutdown(self._connection,False)
         return
      if self._state == 0:
         if not isinstance(packet,Packet.HS_Version):
            if self._talk:
               print("PACKET IS NOT THE TYPE WE WANT IT TO BE (HS_VERSION)")
               print(packet)
            self._shutdown(connection)
         return_packet = Packet.HS_Version(1.0)
         connection.Send(return_packet.wrap().encode())
         if not packet.version == 1.0:
            if self._talk:
               print("Version out of range")
               print(packet)
            self._shutdown(connection)
         self._state = 1
      elif self._state == 1:
         if not isinstance(packet,Packet.HS_Options):
            if self._talk:
               print("PACKET IS NOT THE TYPE WE WANT IT TO BE (HS_OPTIONS)")
               print(packet)
            self._shutdown(connection)
         if not packet.protocol == "TCP":
            if self._talk:
               print("TRYING TO USE NON-TCP TRANSPORT, UNSUPPORTED")
               print(packet)
            self._shutdown(connection)
         self._their_options_packet = packet
         return_packet = Packet.HS_Options(minport=packet.minport,maxport=packet.maxport,
                                          portusage=packet.portusage,protocol="TCP",
                                          timeout=packet.timeout,payload=packet.payload,
                                          key=randint())
         self._my_options_packet = return_packet
         connection.Send(return_packet.wrap().encode())
         self._state = 2
      elif self._state == 2:
         if not isinstance(packet,Packet.HS_Options):
            if self._talk:
               print("PACKET IS NOT THE TYPE WE WANT IT TO BE (HS_OPTIONS)(3RD)")
               print(packet)
               self._shutdown(connection)
         if not packet.key == self._my_options_packet.key:
            if self._talk:
               print("3RD PACKET KEY IS INCORRECT")
               print(self._my_options_packet)
               print(packet)
            self._shutdown(connection)
         return_packet = self._their_options_packet
         connection.Send(return_packet.wrap().encode())
         stateManager = StateManager.StateManager(self._my_options_packet, self._their_options_packet, connection, self._talk)
         connection.Dispatcher.setTarget(PacketTranslator.PacketTranslator(stateManager,self._talk))

