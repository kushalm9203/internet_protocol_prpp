#!/usr/bin/python

# This class defines the HandShake options packet, Handhsake version packet, Data packet, 
# Management packet, and Switching packet. Each packet has its own fields, which are shown below. 
# Packets are encoded using json.

import json
import random

from Mersenne_Twister import MT_RAND_MAX
import Mersenne_Twister

def packet_decoder(packet_type,string):
   """Decides what type of packet is given and return the fields for that packet."""
   dct = json.loads(string)
   if packet_type == HS_Version:
      return HS_Version(dct['version'])
   if packet_type == HS_Options:
      return HS_Options(minport=dct['minport'], maxport=dct['maxport'],
                        portusage=dct['portusage'], protocol=dct['protocol'],
                        timeout=dct['timeout'], payload=dct['payload'],
                        key=dct['key'])
   if packet_type == Data:
      return Data(data=dct['data'], terminate=int(dct['terminate']))
   if packet_type == Management:
      return Management(dct['command'],location=dct['location'])
   if packet_type == Switching:
      return Switching(dct['status'])
   if packet_type == Error:
      return Error()

def as_wrapped_packet(dct):
   """Wrapped packet"""
   packet = Send_Wrapper(HS_Version())
   packet.type = dct['type']
   packet.data = dct['data']
   return packet

class Packet(object):
   """Packet class"""
   def wrap(self):
      """Send the json packet wrapped as a string"""
      return Send_Wrapper(self)
   def encode(self):
      return json.dumps(self.__dict__)
   def __str__(self):
      return json.dumps(self.__dict__)

class Error(Packet):
   """Error packet"""
   def __init__(self):
      return

class Send_Wrapper(Packet):
   """Wrapper class for a packet to give its type and json data as string"""
   def __init__(self, packet):
      self.type = packet.__class__.__name__
      self.data = str(packet)
   def unwrap(self):
      return packet_decoder(eval(self.type),self.data)
   def __str__(self):
      return json.dumps(self.__dict__)

class Switching(Packet):
   """Packet used in switching ports from one connection to another."""
   def __init__(self,status):
      self.status = status

class HS_Version(Packet):
   """Handshake Version Information packet."""
   def __init__(self, version=1.0):
      self.version = version

class HS_Options(Packet):
   """Handshake Connection Options packet.
   minport - smallet port number to begin
   maxport - max port number that can be generated
   portusage - number of packets to sent in a port
   protocol - protocol version to use
   timeout - socket timeout
   paylpoad - payload size
   key - key"""
   def __init__(self, minport=49152, maxport=65335, portusage=100, protocol="TCP", timeout=5, payload=16, key=None):
      self.key = key
      if self.key is None:
         self.key = Mersenne_Twister.MersenneTwister32(int(random.random()*Mersenne_Twister.MT_RAND_MAX)).next()
      self.minport = minport
      self.maxport = maxport
      self.portusage = portusage
      self.protocol = protocol
      self.timeout = timeout
      self.payload = payload

class Data(Packet):
   """Data Payload packet.
   data - payload data to send
   terminate - 0 or 1 to continue or stop sending"""
   def __init__(self, data="", terminate=0):
      self.data = data
      self.terminate = terminate #Terminate the conneciton option. 0 or 1

class Management(Packet):
   """Management packet. Command can be receive, send. Location is the locaation of file to be sent
   command - command to be used. Send/receive
   location- location of file"""
   def __init__(self,command,location=None):
      self.command = command
      self.location = location
