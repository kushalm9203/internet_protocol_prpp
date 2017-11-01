
# This file creates and manages sockets that are used both by the client and the server connections

import socket
import threading
import select
import Queue
import struct

class SocketConnection(object):
    def __init__(self, packetDispatcher,talk=False):
        """Creates a socket connection"""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self._stopEvent = threading.Event()
        self._packetDispatcher = packetDispatcher
        self._packetDispatcher.setConnection(self)
        self._sendQueue = Queue.Queue(100)
        self._sendThread = None
        self._recvThread = None
        self._talk = talk
        self._hostname = '127.0.0.1'

    @staticmethod
    def from_socket(socket, packetDispatcher,talk=False):
        """Used by the Listener and StateManager to pass values to the socket connection"""
        connection = SocketConnection(packetDispatcher,talk)
        connection._socket = socket
        return connection

    def get_peer_address(self):
        """Returns the remote address to which the socket is connected"""
        return self._socket.getpeername()[0]

    def setDispatcher(self,dispatcher):
        """Sets the packetDispatcher for the socket connection"""
        self._packetDispatcher = dispatcher
        if dispatcher is not None:
            self._packetDispatcher.setConnection(self)

    def Connect(self, address, port = 1443):
        """Connects to the remote socket at the 'address'"""
        self._socket.connect((address, port))
        if self._talk:
            print("Connected!")

    def Wait(self, timeout = None):
        """Passes the timeout value to the thread that is either sending or receiving"""
        if self._sendThread:
            self._sendThread.join(timeout)
        if self._recvThread:
            self._recvThread.join(timeout)

    def Start(self):
        """Initializes sending and/or receiving threads"""        
        self._recvThread = threading.Thread(target = self._RecvHandler, name="Recv")
        self._sendThread = threading.Thread(target = self._SendHandler, name="Send")
        self._sendThread.start()
        self._recvThread.start()

    def Shutdown(self, readOnly = False):
        """Shuts down either one or both halves of the socket connection"""
        if readOnly:
            try:
                self._socket.shutdown(socket.SHUT_RD)
            except Exception:
                pass
        else:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass

    def Stop(self):
        """Stops the threads and closes the socket connection"""
        self._sendQueue.put(None)
        self._stopEvent.set()
        self._sendThread.join()
        self._recvThread.join()
        self._socket.close()
        if self._packetDispatcher is not None:
            self._packetDispatcher.Stop()


    def Send(self, packet_string):
        """Puts items in the sending queue"""
        if self._talk:
            print("Sending: " + packet_string)
        length = len(packet_string)
        s = struct.Struct('>I ' + str(length) + 's')
        values = (length, packet_string)
        data = s.pack(*values)
        self._sendQueue.put(data)

    @property
    def Dispatcher(self):
        """Returns the packetDispatcher"""
        return self._packetDispatcher

    def _GotData(self, data):
        """Queues data at packetDispatcher"""
        self._packetDispatcher.QueueData(data)

    def _SendHandler(self):
        """Handles the sending process"""
        while True:
            sendData = self._sendQueue.get()
            if sendData == None:
                if self._talk:
                    print("Send handler shutdown!")
                self._sendQueue.task_done()
                return
            self._socket.sendall(sendData)
            self._sendQueue.task_done()

    def _RecvHandler(self):
        """Handles the receiving process"""
        while self._stopEvent.isSet() == False:
            value = select.select([self._socket], [], [self._socket], 100)
            if len(value[0]) != 0:
                data = self._socket.recv(1024 * 16)
                if len(data) == 0:
                    if self._talk:
                        print("0-byte recv!")
                    if self._stopEvent.isSet() == False:
                        self.Shutdown()
                        self._sendQueue.put(None)
                        self._stopEvent.set()
                        if self._packetDispatcher is not None:
                           self._packetDispatcher.Stop()
                    break
                else:
                    self._GotData(data)
            elif len(value[2]) != 0:
                if self._talk:
                    print("Something went wrong!")
        if self._talk:
            print("Recv handler shutdown!")

