#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import socket


BUFFER_LENGTH = 1024


def run_echo_server(port):
    '''Run echo server on specified port'''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.listen(1)
        (conn, addr_info) = s.accept()
        print("Client %s:%s - connected" % addr_info)
        while(True):
            buff = conn.recv(BUFFER_LENGTH)
            if buff:
                conn.send(buff)
                print(buff, end='')
            else:
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
