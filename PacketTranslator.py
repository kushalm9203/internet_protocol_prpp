
# This class is an intermediate target for receiving packets. It receives the 
# json interpretation of a packet. It translates it to the proper packet type
# and sends it to the target. This packet receives the raw encoding of the Send_Wrapper
# packet. This is the target of a packetDispatcher.

import json

import Packet

class PacketTranslator(object):
    """Packet transaltor class"""
    def __init__(self,target,talk=False):
        self._target = target
        self._talk = talk
   
    def _FullPacketReceived(self,data,connection):
        """ Receive the full packet and unwrap it"""
        packet = json.loads(data, object_hook=Packet.as_wrapped_packet)
        if self._talk:
            print("Recving: " + str(packet))
        packet = packet.unwrap()
        self._target._FullPacketReceived(packet,connection)
