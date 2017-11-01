#!/usr/bin/python


import argparse
import sys
import time

import Client

#Parse command line arguments that are given to client.py
parser = argparse.ArgumentParser()

parser.add_argument("-p","--port",help="port to connect to")
parser.add_argument("-n","--server",help="string FQDN of the remote server")
#parser.add_argument("-S","--send",help="CLI Send command",action="store_true")
#parser.add_argument("-R","--recv",help="CLI Recv command",action="store_true")
#parser.add_argument("-t","--target",help="CLI target of command")
#parser.add_argument("-s","--source",help="CLI source for command")
parser.add_argument("-l","--lower",help="Lower port of requested range")
parser.add_argument("-u","--upper",help="Upper port of reqeusted range")
parser.add_argument("-N","--number",help="Number of packets before switch")
parser.add_argument("-P","--payload",help="Size of data packet payloads")
args = parser.parse_args()


port = 55974 # default server port
server = '127.0.0.1' # default Address of the server
lower = 55600 # default lower port limit
upper = 55700 # default upper port limit
number = 2 # default number of packets to send per port
payload = 16 # default Size of payload
target = None
source = None

# Parse command line inputs
if args.port is not None:
   port = int(args.port)
if args.server is not None:
   server = args.server
if args.lower is not None:
   lower = int(args.lower)
if args.upper is not None:
   upper = int(args.upper)
if args.number is not None:
   number = int(args.number)
if args.payload is not None:
   payload = int(payload)

# Function to establish client connection. 5 attempts are made.
def Connect(client):
   attempt = 0
   maxattempts = 5
   connecting = True
   while connecting:
      try:
         attempt += 1
         client.Connect()
         connecting = False
      except Exception:
         connecting = True
         if attempt >= maxattempts:
            print("Attempted to connect " + str(maxattempts) + " times. Failed.")
            close(client)
   client.Start() # Start client by sending a handshake packet.

# Description of file source. Either from stdin or opening the file.
def fd_source(source):
   if source.upper() == "STDIN":
      return sys.stdin
   else:
      return open(source,'r')

# Description of file to be written. Either stdout or writting to the given file.
def fd_target(target):
   if target.upper() == "STOUT":
      return sys.stdout
   else:
      return open(target,'w')

# Close client
def close(client):
   client.close()
   exit()

# Create client object
args = parser.parse_args()
client = Client.Client(server,port,lower,upper,number,"TCP",5,payload)


# # Checking if client is in either send or receive.
# if args.send or args.recv:
#    if args.send and args.recv:
#       print("Specify only 1 CLI command.")
#       close(client)
#    if args.target is None or args.source is None:
#       print("Running a command via CLI requires a target and a source")
#       close(client)
#    target = args.target
#    source = args.source
#    Connect(client)
#    if args.send: #Send the data in the source file to the target file in server.
#       fd = fd_source(source)
#       client.send(fd,target)
#       close(client)
#    elif args.recv: #Receive the data from file in server to the target file in client, or stdin to stdout if that is specified.
#       fd = fd_target(target)
#       client.recv(fd,source)
#       close(client)


Connect(client)

# Start reading inputs from stdin. These are the commands that the user can give to the client.
# It should be 1 when close is given, or 3 for send and recv.
print("Psuedorandom Port Protocol, Client Interpreter")
looping = True
while looping:
   user_input = raw_input(">>> ").split()
   if len(user_input) != 3 and len(user_input) != 1:
      print("Commands are either 1 or 3 arguments")
   elif user_input[0].lower() == "close":
      client.close()
      looping = False
   elif user_input[0].lower() == "send":
      fd = fd_source(user_input[1])
      client.send(fd,user_input[2])
   elif user_input[0].lower() == "recv":
      fd = fd_target(user_input[2])
      client.recv(fd,user_input[1])
   else:
      print("Unknown command")
   while (client.get_state() != 0):
      time.sleep(1)
