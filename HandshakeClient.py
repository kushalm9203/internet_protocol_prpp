
# This class handles the handshake in the client side.

import random

import Packet
import PacketTranslator
import StateClient
import Mersenne_Twister

def randint():
   """Get a random packet key """
   rand = random.random()
   return int(rand*Mersenne_Twister.MT_RAND_MAX)

class HandshakeClient(object):
   def __init__(self,clientref,options_packet=None):
      """Initialize the handshake client. This class will handle teh handshake in teh cleint side."""
      self._state = 0
      self._options_packet = options_packet
      self._options_packet.key = randint()
      self._clientref = clientref

   def _shutdown(self,connection,send=False):
      """Shuts down the connection"""
      if send:
         connection.Send(Packet.Error().wrap().encode())
      connection.Shutdown()
      connection.Stop()

   def _FullPacketReceived(self,packet,connection):
      """Decides if the 'protocol', 'version', packet types of the client and the server are in agreement with one another."""
      if isinstance(packet,Packet.Error):
         self._shutdown(self._connection,False)
         return
      if self._state == 0:
         if not isinstance(packet,Packet.HS_Version):
            print("PACKET IS NOT THE TYPE WE WANT IT TO BE (HS_VERSION)")
            print(packet)
            self._shutdown(connection)
         if not packet.version == 1.0:
            print("Version out of range")
            print(packet)
            self._shutdown(connection)
         connection.Send(self._options_packet.wrap().encode())
         self._state = 1
      elif self._state == 1:
         if not isinstance(packet,Packet.HS_Options):
            print("PACKET IS NOT THE TYPE WE WANT IT TO BE (HS_OPTIONS)(3RD)")
            print(packet)
            self._shutdown(connection)
         self._their_options_packet = packet
         return_packet = self._their_options_packet
         connection.Send(return_packet.wrap().encode())
         self._state = 2
      elif self._state == 2:
         if not packet.key == self._options_packet.key:
            print("3RD PACKET KEY IS INCORRECT")
            print(self._my_options_packet)
            print(packet)
            self._shutdown(connection) 
         stateManager = StateClient.StateClient(self._options_packet, self._their_options_packet, connection)
         connection.Dispatcher.setTarget(PacketTranslator.PacketTranslator(stateManager))
         self._clientref.setStateManager(stateManager)
