from __future__ import print_function
import sys
import socket
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
from spolkslib import server
from spolkslib import fileutils
from spolkslib import connutils
from spolkslib import protocol
from spolkslib.connutils import URGENT_BYTE

urg_sended = 0


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
