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
# A liitle hack to load lib from top-level
if __name__ == '__main__':
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from spolkslib import server
from spolkslib import fileutils
from spolkslib import connutils
from spolkslib import client

BUFFER_LENGTH = 1024
URGENT_BYTE = '!'

urg_sended = 0
total_bytes_received = 0
_sock = None


def send_progress_handler(sock, count):
    """Called after buffer send"""
    #send urgent data after MB sended
    if (count % (1024 * 1024)) != 0:
        return
    try:
        sock.send(URGENT_BYTE, socket.MSG_OOB)
        time.sleep(0.05)
        print(count, " bytes transfered")
    except socket.error as e:
        print("Send OOB data error %s" % e)
    global urg_sended
    urg_sended += 1


def recv_progress_handler(sock, count):
    global total_bytes_received
    total_bytes_received = count


def urgent_data_handler(signum, frame):
    """Called after received urgent data"""
    try:
        urg_data = _sock.recv(1, socket.MSG_OOB)
        time.sleep(0.001)
        if urg_data == URGENT_BYTE:
            print("URG: Received {} bytes".format(total_bytes_received))
        else:
            print("Unknown urgent value 0X%X received" % (urg_data))
    except socket.error as e:
        print("Receiving urgent data error %s %s" % (e, e.errno))


def handle_server_request(conn, addr, f):
    """
    Handle single request
    conn - socket connection
    addr - addr info
    f - file object to serve
    """
    print("Client %s:%s - connected" % addr)
    try:
        #send file size first
        file_size = fileutils.get_file_size(f)
        packed_size = struct.pack("!Q", file_size)
        if not connutils.send_buffer(conn, packed_size):
            return
        #recv fileseek
        packed_seek_value = connutils.recv_buffer(conn, 8)
        if len(packed_seek_value) != 8:
            return
        seek_value = struct.unpack("!Q", packed_seek_value)
        if not seek_value:
            return
        seek_value = seek_value[0]
        if seek_value:
            f.seek(seek_value, 0)
            print("Seeking to %s" % seek_value)
        #send file content
        transfered = fileutils.transfer_file(conn,
                    f, progress_callback=send_progress_handler)
        print("Bytes send " + str(transfered))
        filesize = fileutils.get_file_size(f)
        if transfered != filesize - seek_value:
            print("!! Not all data has been sent !!")
    except socket.error as e:
        print("handle_server_request error %s" % e)
    finally:
        f.seek(0)
        conn.close()
        print("Client %s:%s - disconnected" % addr)


def serve_file(port, f):
    """
    Run server on port to serve file f
    Raise exception if fails
    """
    print("Server ran...")
    server_socket = None
    try:
        server_socket = server.create_local_server(port)
        while(True):
            (conn, addr_info) = server_socket.accept()
            handle_server_request(conn, addr_info, f)

    except socket.error, e:
        print("Socket error: %s" % (e))
    except Exception as e:
        print("Server Exception %s" % e)
    finally:
        print("sended urgent %s" % urg_sended)
        if server_socket:
            server_socket.close()
        print("Shutdown server")


def get_file_from_server(host, port, filename, flag_overwrite=False):
    global _sock
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print("Error creating client socket")
        return
    try:
        client_socket.connect((host, port))
    except socket.error as e:
        client_socket.close()
        print("error connecting to server: %s" % e)
        return
    _sock = client_socket
    signal.signal(signal.SIGURG, urgent_data_handler)
    fcntl.fcntl(client_socket.fileno(), fcntl.F_SETOWN, os.getpid())
    try:
        #get file size
        packed_size = connutils.recv_buffer(client_socket, 8)
        if len(packed_size) != 8:
            return
        #unpack long long format
        server_filesize = struct.unpack("!Q", packed_size)
        if not server_filesize:
            print("Error receiving filesize")
            return
        server_filesize = server_filesize[0]
        print("Server file size %s" % server_filesize)
        try:
            (f, seek_value) = client.create_client_file(filename,
                            server_filesize, flag_overwrite)
        except client.ClientError as e:
            print("Create file error: %s" % e)
            return

        packed_seek = struct.pack("!Q", seek_value)
        if not connutils.send_buffer(client_socket, packed_seek):
            f.close()
            return

        print("Receiving file...")
        bytes_received = fileutils.recv_file(client_socket, f,
            server_filesize-seek_value, progress_callback=recv_progress_handler)
        print("Bytes received %s" % bytes_received)
        if (bytes_received + seek_value) != server_filesize:
            print("!!Not all data received!!")
        f.close()
    except Exception as e:
        print("Client Disconnected: %s" % e)
    finally:
        signal.signal(signal.SIGURG, signal.SIG_DFL)
        client_socket.close()


    #arg parsing

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
