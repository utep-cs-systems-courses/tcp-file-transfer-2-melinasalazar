#! /usr/bin/env python3

import sys, re, socket, os

sys.path.append("../lib")  # for params
sys.path.append("../framed-echo") # for framedSock

from framedSock import framedSend, framedReceive

import params

os.chdir("ServerFiles")  # Save files here

switchesVarDefaults = (
    (('-l', '--listenPort'), 'listenPort', 50001),
    (('-d', '--debug'), "debug", False),  # boolean (set if present)
    (('-?', '--usage'), "usage", False),  # boolean (set if present)
)

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)

while True:
    print("listening on:", bindAddr)

    sock, addr = lsock.accept()  # Accept incoming connections

    rc = os.fork()  # Ready to fork multiple connections
    if rc == 0:
        print("connection rec'd from", addr)

        start = framedReceive(sock, debug)  # Ready to receive from client
        print("Received File!\n")

        try:
            start = start.decode()
        except AttributeError:
            print("error exiting: ", start)
            sys.exit(0)

        count = 0  # Check for file characters
        for char in start:
            if char.isalpha():
                break
            else:
                count = count + 1
        start = start[count:]

        start = start.split("\'s\'")  # Check for packet that starts with's' (Enconding)

        file = open(start[0].strip(), "wb+")  # Open the file and write output

        while True:
            try:
                packet = framedReceive(sock, debug)
            except:
                pass

            if debug: print("rec'd: ", packet)
            if not packet:
                break

            if b"\'e\'" in packet:  # Last (Encoding) packet
                file.close()
                sys.exit(0)
            else:
                file.write(packet[1:])
        break