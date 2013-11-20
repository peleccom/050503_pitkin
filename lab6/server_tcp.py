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
    except socket.error as e:
        print("Send OOB data error %s" % e)
    global urg_sended
    urg_sended += 1


def handle_server_request(server_socket, f):
    """
    f - file object to serve
    """
    client_sockets = []
    #client_info = {
    #"soket" :
    #{"addr":"addr",
    #"seek": 0, "can_write": False, "size_sended": False,"sended":0}
    #}
    client_info = {}
    file_size = fileutils.get_file_size(f)
    packed_size = struct.pack("!Q", file_size)
    buf_size = 1024
    try:
        while True:
            [rfd, wfd, xfd] = select.select([server_socket] + client_sockets,
                client_sockets, client_sockets)
            for r_socket in rfd:
                if server_socket == r_socket:
                    #new connection arrived
                    (conn, addr_info) = server_socket.accept()
                    print("Client %s:%s - connected" % addr_info)
                    client_info[conn] = {
                        "addr": addr_info,
                        "seek": 0,
                        "size_sended": False,
                        "seek_received": False,
                        "sended": 0,
                    }
                    client_sockets.append(conn)
                else:
                    #client socket read
                    if not client_info[r_socket]["size_sended"]:
                        continue
                    if client_info[r_socket]["seek_received"]:
                        continue
                    client_info_record = client_info[r_socket]
                    print("Read request from %s:%s" %
                            client_info_record["addr"])
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
                    client_info_record["seek"] = seek_value
                    client_info_record["seek_received"] = True
            for w_socket in wfd:
                if not client_info[w_socket]["size_sended"]:
                    if connutils.send_buffer(w_socket, packed_size):
                        client_info[w_socket]["size_sended"] = True
                    else:
                        print("error while send size to %s" %
                            (client_info[w_socket]["addr"]))
                        client_sockets.remove(wsocket)
                        del client_info[wsocket]
                        wsocket.close()
                    continue
                if not client_info[w_socket]["seek_received"]:
                    continue
                #write chunk of data
                client_info_record = client_info[w_socket]
                seek_value = client_info_record["seek"]
                f.seek(seek_value, 0)
                print("%s: seeking to %s" %
                    (client_info_record["addr"], seek_value))
                buffer = f.read(buf_size)
                client_info_record["seek"] = f.tell()
                need_send = len(buffer)
                if not need_send:
                    client_sockets.remove(w_socket)
                    del client_info[w_socket]
                    w_socket.close()
                    print("Client %s disconnected" %
                        (client_info_record["addr"],))
                    continue
                if not connutils.send_buffer(w_socket, buffer):
                    print("Error while send chunk to %s. disconnect" %
                        (client_info_record["addr"],))
                    client_sockets.remove(w_socket)
                    del client_info[w_socket]
                    w_socket.close()
                    continue
                client_info_record["sended"] += need_send
                send_progress_handler(w_socket, client_info_record["sended"])

    finally:
        for client_socket in client_sockets:
            print("Close socket connection %s" %
                [client_info[client_socket]["addr"]])


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
