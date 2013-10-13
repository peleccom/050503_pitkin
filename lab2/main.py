#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import os
import socket

# A liitle hack to load lever from top-level
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
        s = server.create__local_server(port)
        try:
            (conn, addr_info) = s.accept()
        except KeyboardInterrupt, e:
            print("Accept interrupted by user")
            s.close()
            return
        print("Client %s:%s - connected" % addr_info)
        while(True):
            try:
                buff = conn.recv(BUFFER_LENGTH)
            except KeyboardInterrupt, e:
                print("Receive interrupted by user")
                conn.close()
                s.close()
                return
            if buff:
                conn.send(buff)
                print(buff, end='')
            else:
                break
            if buff.strip() == "!quit":
                print("\nShutdown command recognized")
                conn.send("Shutdown")
                conn.shutdown(socket.SHUT_RDWR)
                break
        print("\nClient %s:%s - disconnected" % addr_info)
        conn.close()
        s.close()
    except socket.error, e:
        print("Socket error: %s" % (e))


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
