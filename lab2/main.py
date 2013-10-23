#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import os
import socket

# A liitle hack to load lib from top-level
if __name__ == '__main__':
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from spolkslib import server

BUFFER_LENGTH = 1024


def run_echo_server(port):
    '''Run echo server on specified port
       raise ValueError if port not in range 0-65535
    '''
    try:
        s = server.create_local_server(port)
    except:
        print("Can't create server")
        sys.exit(1)
    try:
        while(True):
            (conn, addr_info) = s.accept()
            print("Client %s:%s - connected" % addr_info)
            try:
                while(True):
                    buff = conn.recv(BUFFER_LENGTH)
                    if buff:
                        conn.send(buff)
                        print(buff, end='')
                    else:
                        break
                    if buff.rstrip() == "!quit":
                        print("\nShutdown command recognized")
                        conn.send("Shutdown")
                        conn.shutdown(socket.SHUT_RDWR)
                        break
            finally:
                conn.close()
                print("\nClient %s:%s - disconnected" % addr_info)
    except socket.error as e:
        print("Socket error: %s" % (e))
    except KeyboardInterrupt as e:
        print("Server interrupted")
    finally:
        print("Shutdown server")
        s.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: main.py <port>")
        sys.exit(2)
    try:
        port = int(sys.argv[1])
        run_echo_server(port)
    except ValueError, e:
        print("Incorrect port value")


if __name__ == '__main__':
    main()
