
# This class creates the Server object.
import threading

import Listener

class Server(object):
   """The Server object is created and _listener, _listener_thread and _stopEvent are initialized"""
   def __init__(self, bindport, listen_number,verbose=False):
      self._stopEvent = threading.Event()
      self._listener = Listener.Listener(bindport, listen_number, self._stopEvent,verbose)
      self._listener_thread = threading.Thread(target=self._listener.Start, name="Listener")

   def Stop(self):
      self._stopEvent.set()
      self._listener_thread.join()

   def Start(self):
      self._listener_thread.start()

if __name__ == "__main__":
   s = Server(55974,5)
   s.Start()
   print("server started, check if it's up, 55974")
   print("press enter to close the server, or at least try to")
   raw_input("")
   print("server stopping")
   s.Stop()
   print("server should have stopped, check that it's down")
