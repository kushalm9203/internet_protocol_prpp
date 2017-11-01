#!/usr/bin/python

import argparse

import Server


parser = argparse.ArgumentParser(description="Run a Pseudorandom Port Protocol Server")

parser.add_argument("-p","--port",help="listen port")
parser.add_argument("-L","--listeners",help="size of listener queue")
parser.add_argument("-v","--verbose",help="talk about packets",action="store_true")
args = parser.parse_args()


p = 55974 # default listen port
L = 5 # default size of listener queue
verbose = args.verbose # default verbose value is 'True'

# Parse command line inputs
if args.port is not None:
   p = int(args.port)
if args.listeners is not None:
   L = int(args.listeners)

server = Server.Server(p,L,verbose)
server.Start()
raw_input("Server is running. Press enter to stop the server.")
server.Stop()

