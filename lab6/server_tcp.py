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


def handle_server_request(server_socket, f):
    """
    f - file object to serve
    """
    client_sockets = []
    addr_infos = {}
    client_seeks = {}
    can_write = []
    file_size = fileutils.get_file_size(f)
    packed_size = struct.pack("!Q", file_size)
    buf_size = 1024
    try:
        while True:
            [rfd, wfd, xfd] = select.select([server_socket] + client_sockets,
                client_sockets, client_sockets)
            for r_socket in rfd:
                if server_socket  == r_socket:
                    (conn, addr_info) = server_socket.accept()
                    print("Client %s:%s - connected" % addr_info)
                    client_sockets.append(conn)
                    addr_infos[conn] = addr_info
                    #send file size first
                    if not connutils.send_buffer(conn, packed_size):
                        return
                else:
                    print("Read request from %s:%s" % addr_infos[r_socket])
                    #recv fileseek
                    packed_seek_value = connutils.recv_buffer(r_socket, 8)
                    if len(packed_seek_value) != 8:
                        r_socket.close()
                        client_sockets.remove(r_socket)
                        continue
                    seek_value = struct.unpack("!Q", packed_seek_value)
                    if not seek_value:
                        r_socket.close()
                        client_sockets.remove(r_socket)
                        continue
                    seek_value = seek_value[0]
                    f.seek(seek_value, 0)
                    print("Seeking to %s" % seek_value)
                    buffer = f.read(buf_size)
                    client_seeks[r_socket] = f.tell()
                    print("save")
                    need_send = len(buffer)
                    if not need_send:
                        r_socket.close()
                        client_sockets.remove(r_socket)
                        continue
                    if not connutils.send_buffer(r_socket, buffer):
                        r_socket.close()
                        client_sockets.remove(r_socket)
                        continue
                    can_write.append(r_socket)
            for w_socket in wfd:
                if  w_socket not in can_write:
                    continue
                print("Write to %s" % [addr_infos[w_socket]])
                seek_value = client_seeks[w_socket]
                f.seek(seek_value, 0)
                print("Seeking to %s" % seek_value)
                buffer = f.read(buf_size)
                print("s")
                client_seeks[w_socket] = f.tell()
                need_send = len(buffer)
                if not need_send:
                    w_socket.close()
                    client_sockets.remove(w_socket)
                    continue
                if not connutils.send_buffer(w_socket, buffer):
                    w_socket.close()
                    client_sockets.remove(w_socket)
                    continue
    finally:
        for client_socket in client_sockets:
            print("Close socket connection %s" % [addr_infos[client_socket]])

def serve_file(port, f):
    """
    Run server on port to serve file f
    Raise exception if fails
    """
    print("Server ran...")
    server_socket = None
    try:
        server_socket = server.create_local_server(port)
        handle_server_request(server_socket, f)
    except socket.error, e:
        print("Socket error: %s" % (e))
    except Exception as e:
        print("Server Exception %s" % e)
        traceback.print_exc()
    finally:
        print("sended urgent %s" % urg_sended)
        if server_socket:
            server_socket.close()
        print("Shutdown server")
