
# This file creates the listener that is used by the Server (on multiple threads).

import socket
import select
import threading

import PacketTranslator
import HandshakeManager
import PacketDispatcher
import SocketManager


class Listener(object):
   """Listener used by the Server to listen for connections from clients"""
   def __init__(self,bind_port,listen_number,threadEvent,verbose=False):
      self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
      self._stopEvent = threadEvent
      self._hostname = '127.0.0.1'
      self._bindPort = bind_port
      self._listenNumber = listen_number
      self._talk = verbose


   def Start(self):
      """Starts listening on the default port and accepts client connections"""
      self._socket.bind((self._hostname,self._bindPort))
      self._socket.listen(self._listenNumber)
      read_sockets = [self._socket]
      while self._stopEvent.isSet() == False:
         readable, writeable, errored = select.select(read_sockets, [], [], 1)
         for sock in readable:
            (clientsocket, address) = sock.accept()
            handshaker = HandshakeManager.HandshakeManager(verbose=self._talk) ## Manage the handshake for server
            dispatcher = PacketDispatcher.PacketDispatcher() 
            dispatcher.Start(PacketTranslator.PacketTranslator(handshaker,self._talk))
            new_connection = SocketManager.SocketConnection.from_socket(clientsocket,dispatcher,self._talk) ## Start new connection 
            new_connection.Start()
            print("Connection Created!")
      self._socket.close()         
