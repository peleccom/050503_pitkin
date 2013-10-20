#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import socket
import argparse
import os
# A liitle hack to load lib from top-level
if __name__ == '__main__':
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from spolkslib import server

BUFFER_LENGTH = 1024


def create_server(port):
    try:
        server_socket = server.create_local_server(port)
        try:
            (conn, addr_info) = server_socket.accept()
        except KeyboardInterrupt, e:
            print("Accept interrupted by user")
            server_socket.close()
            return
        print("Client %s:%s - connected" % addr_info)
    except socket.error, e:
        print("Socket error: %s" % (e))


def server_command(args):
    print("Run server..")


def client_command(args):
    print("Run client..")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Select mode')
    parser_server = subparsers.add_parser("server", help="Run as server")
    parser_client = subparsers.add_parser("client", help="Run as client")
    parser_server.add_argument("port")
    parser_server.add_argument("-r", help="Filename to read from",
        required=True, metavar="filename")
    parser_server.set_defaults(func=server_command)
    parser_client.add_argument("host")
    parser_client.add_argument("port")
    parser_client.add_argument("-w", help="Filename to write",
        required=True, metavar="filename ")
    parser_client.set_defaults(func=client_command)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
