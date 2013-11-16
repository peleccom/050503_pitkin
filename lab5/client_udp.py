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
import select

sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from spolkslib import fileutils
from spolkslib import connutils
from spolkslib import client
from spolkslib import protocol
from spolkslib.protocol import MyDatagram, MyCommandProtocol


def recv_progress_handler(sock, count):
    print("received %s bytes" % count)


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
        if not server_filesize:
            return
        print("Server file size %s" % server_filesize)
        try:
            (f, seek_value) = client.create_client_file(filename,
                            server_filesize, flag_overwrite)
        except client.ClientError as e:
            print("Create file error %s" % e)
            return
        try:
            bytes_received = fileutils.recv_file_udp(client_socket, f,
                server_filesize - seek_value, myDatagram,
                progress_callback=recv_progress_handler)
        finally:
            f.close()
        print("Bytes received %s" % bytes_received)
        if (bytes_received + seek_value) != server_filesize:
            print("!!Not all data received!!")
    except client.UdpClientError as e:
        print("Udp client error: %s" % e)
    except Exception as e:
        print("Client disconnected: %s" % e)
    finally:
        client_socket.close()
