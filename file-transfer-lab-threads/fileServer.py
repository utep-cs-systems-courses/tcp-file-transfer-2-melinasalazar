import os
import socket, sys
import threading
import time
from threading import Thread

DIRPATH = "./lib"
sys.path.append(DIRPATH)  # for params
import params
from framedSocket import framedSocket

HOST = "127.0.0.1"
PATH_FILES = "./ReceiveFiles/"
CONFIRM_MSG = "file %s received from %s"

# setup
switchesVarDefaults = (
    (('-l', '--listenPort'), 'listenPort', 50001),
    (('-d', '--debug'), "debug", False),  # boolean (set if present)
    (('-?', '--usage'), "usage", False),  # boolean (set if present)
)

paramMap = params.parseParams(switchesVarDefaults)
debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

bind_addr = (HOST, listenPort)

# creating listening socket
listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# associating socket with host and port number
listen_socket.bind(bind_addr)

# "makes" listening socket with max connection to 5
listen_socket.listen(5)
print("listening on: ", bind_addr)

# make lock
lock = threading.Lock()


class Server(Thread):
    def __init__(self, sockAddr):
        Thread.__init__(self)
        self.sock, self.addr = sockAddr
        self.fsock = framedSocket(sockAddr)

    def write_file(self, filename, file_content):
        try:
            # check if dir to receive files exists, if not create it
            if not os.path.exists(PATH_FILES):
                os.makedirs(PATH_FILES)

            # create file to write
            file_writer = open(PATH_FILES + filename, 'w+b')
            file_writer.write(file_content)

            # close and print confirmation msg on server
            file_writer.close()
            print(CONFIRM_MSG % (filename, self.addr))
        except FileNotFoundError:
            print("ERROR: file %s not found " % filename)
            # send failed status
            self.fsock.send_status(0, debug)
            sys.exit(1)

    def run(self):
        print("new thread handling connection from", self.addr)
        while True:
            try:
                # received data from client
                filename, file_content = self.fsock.receive(debug)
            except:
                print("ERROR: file transfer failed")
                # send failed status
                self.fsock.send_status(0, debug)
                self.fsock.close()
                sys.exit(1)

            if debug: print("rec'd: ", file_content)

            # if data was not received, the client has closed:
            if filename is None or file_content is None:
                print("client ", self.addr, " disconnected")
                sys.exit(0)

            # lock section
            lock.acquire()
            if debug:
                time.sleep(5)

            # write file and save it to folder
            filename = filename.decode()
            print(self.addr, " will attempt to save file %s" % filename)
            self.write_file(filename, file_content)

            # success status and close
            self.fsock.send_status(1, debug)
            lock.release()
            # end of lock section


def main():
    while True:
        sock_addr = listen_socket.accept()
        server = Server(sock_addr)
        server.start()


if __name__ == "__main__":
    main()
