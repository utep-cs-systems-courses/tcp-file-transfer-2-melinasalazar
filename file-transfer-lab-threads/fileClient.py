#! /usr/bin/env python3

import socket, sys, re, os
sys.path.append("../lib") 

import params

from framedSock import framedSend, framedReceive

switchesVarDefaults = (
    (('-s', '--server'), 'server', "127.0.0.1:50001"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)

server, usage, debug  = paramMap["server"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()


try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

port = input("Do you want to use the proxy?\n")
if "yes" in port:
    port = "50000"
else:
    port = "50001"

s = None
for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
        print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
        s = socket.socket(af, socktype, proto)
    except socket.error as msg:
        print(" error: %s" % msg)
        s = None
        continue
    try:
        print(" attempting to connect to %s" % repr(sa))
        s.connect(sa)
    except socket.error as msg:
        print(" error: %s" % msg)
        s.close()
        s = None
        continue
    break

if s is None:
    print('could not open socket')
    sys.exit(1)

fileName =  input("Enter the file name:\n") 

try:
    with open(fileName.strip(),"rb") as inputFile:
         data = inputFile.read() # Read file

except FileNotFoundError:
    print("File not found!")
    sys.exit(0) #Exit program if the file is not found

try:
    framedSend(s,b':' +fileName.strip().encode('utf-8') + b"\'s\'")
except BrokenPipeError:
    print("Error: Disconnected")
    sys.exit(0) #Disconnect from server or client

while len(data) >= 100:
    line = data[:100]
    data = data[100:]
    try:
        framedSend(s,b":"+line,debug)
    except BrokenPipeError:
        print("Error: Disconnected")
        sys.exit(0)

if len(data) > 0:
    framedSend(s,b":"+data,debug) # Check for last bytes in file

try:
    framedSend(s,b":\'e\'") # Send last packet message as 'e'
except BrokenPipeError:
    print("Error: Disconnected")
    sys.exit(0)
