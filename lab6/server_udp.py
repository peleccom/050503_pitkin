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
from spolkslib import client
from spolkslib import protocol
from spolkslib.protocol import MyDatagram, MyCommandProtocol


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
        command = datagram_dict['data']
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
            rfd, wfd, xfd = select.select([server_socket], [], [])
            if server_socket in rfd:
                handle_server_request(server_socket, f, file_size, myDatagram)

    except socket.error, e:
        print("Socket error: %s" % (e))
    except Exception as e:
        print("Server Exception %s" % e)
        traceback.print_exc()
    finally:
        if server_socket:
            server_socket.close()
        print("Shutdown server")
