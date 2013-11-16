#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import socket
import argparse
import os
import struct
import time
import signal
import fcntl
import errno
import traceback
import pdb

# A liitle hack to load lib from top-level
if __name__ == '__main__':
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from spolkslib import server
from spolkslib import fileutils
from spolkslib import connutils
from spolkslib import client
from spolkslib import protocol
from spolkslib.protocol import MyDatagram, MyCommandProtocol

BUFFER_LENGTH = 1024

PROTOCOL_COMMAND_RECORD_SIZE = 12
# 4 byte commands
PROTOCOL_COMMAND_SEEK = 'SEEK'
PROTOCOL_COMMAND_SIZE = 'SIZE'

_server_file_size = None
_client_file = None


def recv_progress_handler(sock, count):
    #if _server_file_size > _client_file.tell():
    #    #send seek request
    #    protocol_send_seek(sock, _client_file.tell())
    print("received %s bytes" % count)


def handle_server_request(conn, f, file_size, myDatagram):
    """
    Handle single request
    conn - socket connection
    f - file object to serve
    """
    try:
        (buffer, addr) = connutils.recv_buffer_from(conn,
                myDatagram.calculate_datagram_size(
                    MyCommandProtocol.SIZE_COMMAND_SIZE))
        datagram_dict = myDatagram.unpack(buffer)
        command  = datagram_dict['data']
        command_type = MyCommandProtocol.recognize_command(command)
        if command_type == protocol.PROTOCOL_COMMAND_SIZE:
            # send size to client
            print("Size response for address %s" % (addr,))
            command = MyCommandProtocol.size_response(file_size)
            buffer = myDatagram.pack(command)
            connutils.send_buffer_to(conn, buffer, addr)

            return
        elif command_type == protocol.PROTOCOL_COMMAND_SEEK:
            # seek in file and send content
            seek_value = MyCommandProtocol.unpack_seek_command(command)
            if not (seek_value is None):
                print("Seeking to %s for address %s" % (seek_value, addr))
                f.seek(seek_value, 0)
            buffer = f.read(protocol.BUFFER_SIZE)
            need_send = len(buffer)
            if not need_send:
                return
            command = MyCommandProtocol.data_response(buffer)
            buffer = myDatagram.pack(command)
            connutils.send_buffer_to(conn, buffer, addr)
            #send file content
            return
    except socket.error as e:
        print("handle_server_request error %s" % e)


def serve_file(port, f):
    """
    Run server on port to serve file f
    Raise exception if fails
    """
    print("Server ran...")
    server_socket = None
    try:
        server_socket = server.create_local_server(port, True)
        file_size = fileutils.get_file_size(f)
        myDatagram = MyDatagram(server=True)
        while(True):
            handle_server_request(server_socket, f, file_size,myDatagram)

    except socket.error, e:
        print("Socket error: %s" % (e))
    except Exception as e:
        print("Server Exception %s" % e)
        traceback.print_exc()
    finally:
        if server_socket:
            server_socket.close()
        print("Shutdown server")


def get_file_from_server(host, port, filename, flag_overwrite=False):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error as e:
        print("Error creating client socket")
        return
    try:
        client_socket.connect((host, port))
    except socket.error as e:
        client_socket.close()
        print("error connecting to server: %s" % e)
        return
    try:
        #get file size
        myDatagram = protocol.MyDatagram()
        server_filesize = myDatagram.send_request_blocking(client_socket,
                protocol.PROTOCOL_COMMAND_SIZE)
        if not server_filesize: return
        print("Server file size %s" % server_filesize)
        try:
            (f, seek_value) = client.create_client_file(filename,
                            server_filesize, flag_overwrite)
        except client.ClientError as e:
            print("Create file error %s" % e)
            return
        try:
            bytes_received = fileutils.recv_file_udp(client_socket, f,
                    server_filesize - seek_value, myDatagram, progress_callback=recv_progress_handler)
        finally:
            f.close()
        print("Bytes received %s" % bytes_received)
        if (bytes_received + seek_value) != server_filesize:
            print("!!Not all data received!!")
    except client.UdpClientError as e:
        print("Udp client error: %s" % e)
    except Exception as e:
        print("Client Disconnected: %s" % e)
    finally:
        client_socket.close()


def server_command(args):
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
        sys.exit(1)
    except KeyboardInterrupt as e:
        print("Server interruped by user")
        sys.exit(1)
    finally:
        f.close()


def client_command(args):
    try:
        get_file_from_server(args.host, args.port, args.w, args.overwrite)
    except KeyboardInterrupt as e:
        print("Client interrupted")


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
    parser_client.add_argument("-o", "--overwrite",
        help="Rewrite file if exists", action="store_true")
    parser_client.set_defaults(func=client_command)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
