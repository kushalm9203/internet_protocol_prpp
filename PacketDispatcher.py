
# This file serves the purpose of getting the packets from the connection and
# assembles them into full packets.


import Queue
import threading
import struct

class _PacketDispatcherWorkerThread(threading.Thread):
    """Thread for multithreadded dispatch. Unused"""
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
        threading.Thread.__init__(self)
        
    def run(self):
        while self._dispatcher._stopEvent.isSet() == False:
            data = self._dispatcher._dataQueue.get()
            with self._dispatcher._dataLock:
                if self._dispatcher._isPacketInProgress:
                    if len(data) + len(self._dispatcher._packetBuffer) > self._dispatcher._targetLength:
                        neededLength = self._dispatcher._targetLength - len(self._dispatcher._packetBuffer)
                        self._dispatcher._packetBuffer += data[:neededLength]
                        self._dispatcher._target._FullPacketReceived(self._dispatcher._packetBuffer,
                                                                           self._dispatcher._connection)
                        data = data[neededLength:]
                    else:
                        self._dispatcher._packetBuffer += data
                        if self._dispatcher._targetLength == len(self._dispatcher._packetBuffer):
                            self._dispatcher._target._FullPacketReceived(self._dispatcher._packetBuffer,
                                                                           self._dispatcher._connection)
                            self._dispatcher._isPacketInProgress = False
                            self._dispatcher._packetBuffer = ''
                            self._dispatcher._targetLength = 0
                            continue
                        else:
                            continue
            while True:
                dataLength = struct.unpack('>I', data[:4])[0]
                if len(data) - 4 == dataLength:
                    self._dispatcher._target._FullPacketReceived(data[4:],
                                                                  self._dispatcher._connection)
                    break
                elif len(data) - 4 > dataLength:
                    self._dispatcher._target._FullPacketReceived(data[4:dataLength+4],
                                                                  self._dispatcher._connection)
                    data = data[dataLength + 4:]
                else:
                    with self._dispatcher._dataLock:
                        self._dispatcher._isPacketInProgress = True
                        self._dispatcher._packetBuffer = data[4:]
                        self._dispatcher._targetLength = dataLength
                    break

class PacketDispatcher(object):
    """Assembles data into a complete packet"""
    def __init__(self):
        self._dataQueue = Queue.Queue()
        self._packetBuffer = ''
        self._isPacketInProgress = False
        self._targetLength = 0
        self._handlerThread = None
        self._target = None
        self._connection = None
        self._hasStub = False
    
    def setConnection(self, connection):
        """A 'connection' is conected to the dispatcher"""
        self._connection = connection

    def setTarget(self, target):
        """The 'target' that is using the dispatcher is set"""
        self._target = target

    def QueueData(self, data):
        """'Puts' data in the queue"""
        self._dataQueue.put(data)
        
    def Start(self, target):
        """Starts the handlerThread"""
        self._target = target
        self._handlerThread = threading.Thread(target=self._HandlerProc,name="Dispatcher")
        self._handlerThread.start()
        
    def Wait(self, timeout = None):
        """Sets the timeout for the handlerThread"""
        return self._handlerThread.join(timeout)
    
    def Stop(self):
        """End of queue"""
        self._dataQueue.put(None)
        
    def _HandlerProc(self):
        """Handles dispatcher"""
        while True:
            data = self._dataQueue.get() ## Gets (and removes) item from the queue
            if data == None:
                return
            if self._hasStub:            ## Add the data to packetBuffer if the length of packetBuffer is less than 4
                self._packetBuffer += data
                if len(self._packetBuffer) > 4:
                    self._hasStub = False
                    data = self._packetBuffer
                    self._packetBuffer = ''
            if self._isPacketInProgress: ## Check if packet is still in "progress"
                if len(data) + len(self._packetBuffer) > self._targetLength:  ## Split the data in packetBuffer and denote FullPacketReceived if packetBuffer is larger than the target's needed length
                    neededLength = self._targetLength - len(self._packetBuffer)
                    self._packetBuffer += data[:neededLength]
                    self._target._FullPacketReceived(self._packetBuffer, self._connection)
                    data = data[neededLength:]
                    self._isPacketInProgress = False
                    self._packetBuffer = ''
                    self._targetLength = 0
                else:
                    self._packetBuffer += data
                    if self._targetLength == len(self._packetBuffer):     ## Denote FullPacketReceived if the length of packetBuffer is equal to the target's needed length  
                        self._target._FullPacketReceived(self._packetBuffer, self._connection)  
                        self._isPacketInProgress = False
                        self._packetBuffer = ''
                        self._targetLength = 0
                        continue
                    else:
                        continue
            while True:
                if len(data) < 4:   ## Give 'data' to packetBuffer if the length of data is less than 4
                    self._packetBuffer = data
                    self._hasStub = True
                    break
                dataLength = struct.unpack('>I', data[:4])[0]
                if len(data) - 4 == dataLength:  
                    self._target._FullPacketReceived(data[4:],self._connection)
                    break
                elif len(data) - 4 > dataLength:
                    self._target._FullPacketReceived(data[4:dataLength+4],self._connection)
                    data = data[dataLength + 4:]
                else:
                    self._isPacketInProgress = True
                    self._packetBuffer = data[4:]
                    self._targetLength = dataLength
                    break
