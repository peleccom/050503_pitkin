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
from spolkslib.connutils import URGENT_BYTE

total_bytes_received = 0
_sock = None


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
        bytes_received = fileutils.recv_file(client_socket, f, server_filesize
                - seek_value, progress_callback=recv_progress_handler)
        print("Bytes received %s" % bytes_received)
        if (bytes_received + seek_value) != server_filesize:
            print("!!Not all data received!!")
        f.close()
    except Exception as e:
        print("Client Disconnected: %s" % e)
    finally:
        signal.signal(signal.SIGURG, signal.SIG_DFL)
        client_socket.close()
