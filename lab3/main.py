#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import socket
import argparse
import os
import struct
# A liitle hack to load lib from top-level
if __name__ == '__main__':
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from spolkslib import server
from spolkslib import fileutils

BUFFER_LENGTH = 1024


def serve_file(port, f):
    '''Run server on port to serve file f
    Raise exception if fails'''
    try:
        server_socket = server.create_local_server(port)
        while(True):
            try:
                (conn, addr_info) = server_socket.accept()
            except KeyboardInterrupt, e:
                print("Accept interrupted by user")
                server_socket.close()
                return
            print("Client %s:%s - connected" % addr_info)

            #send file size first
            file_size = fileutils.get_file_size(f)
            packed_size = struct.pack("!Q", file_size)
            sended = conn.send(packed_size)
            while (sended < len(packed_size)):
                packed_size = packed_size[bytes_send:]
                sended = sock.send(packed_size)

            #send file content
            transfered = fileutils.transfer_file(conn, f)
            print("bytes " + str(transfered))
            if transfered != fileutils.get_file_size(f):
                print("eerror")
            f.seek(0)
            conn.close()
    except socket.error, e:
        print("Socket error: %s" % (e))


def get_file_from_server(host, port, f):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    packed_size = client_socket.recv(8)
    print("Receiving file...\nfilesize - %s bytes"
        % struct.unpack("!Q", packed_size))
    client_socket.close()


def server_command(args):
    print("Run server..")
    try:
        f = open(args.r, "rb")
    except IOError, e:
        # exit
        print("Can't open file")
        sys.exit(1)
    try:
        serve_file(args.port, f)
    except Exception, e:
        print(e)
    finally:
        f.close()


def client_command(args):
    print("Run client..")
    try:
        f = open(args.w, "wb")
    except IOEror, e:
        print("Can't open file")
        sys.exit(1)
    try:
        get_file_from_server(args.host, args.port, f)
    except Exception, e:
        print(e)
    finally:
        f.close()


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Select mode')
    parser_server = subparsers.add_parser("server", help="Run as server")
    parser_client = subparsers.add_parser("client", help="Run as client")
    parser_server.add_argument("port", type=int)
    parser_server.add_argument("-r", help="Filename to read from",
        required=True, metavar="filename")
    parser_server.set_defaults(func=server_command)
    parser_client.add_argument("host")
    parser_client.add_argument("port", type=int)
    parser_client.add_argument("-w", help="Filename to write",
        required=True, metavar="filename ")
    parser_client.set_defaults(func=client_command)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
