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
import threading

sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from spolkslib import server
from spolkslib import fileutils
from spolkslib import connutils
from spolkslib import protocol
from spolkslib.connutils import URGENT_BYTE

urg_sended = 0


class KilledThreadException(Exception):
    pass


class ServerThread(threading.Thread):
    def __init__(self, conn, addr_info, f):
        threading.Thread.__init__(self)
        self._f = f
        self._conn = conn
        self._addr_info = addr_info
        self._urg_sended = 0
        self._killed = False

    def run(self):
        self.handle_server_request(self._conn, self._addr_info, self._f)

    def send_progress_handler(self, sock, count):
        """Called after buffer send"""
        #send urgent data after MB sended
        if (count % (1024 * 1024)) != 0:
            return
        if self._killed:
            raise KilledThreadException("thread killed by main programm")
        try:
            sock.send(URGENT_BYTE, socket.MSG_OOB)
            time.sleep(0.05)
            self._urg_sended += 1
            print("%s: %s bytes transfered" % (self._addr_info, count))
        except socket.error as e:
            print("%s: Send OOB data error %s" % (self._addr, e))

    def handle_server_request(self, conn, addr, f):
        """
        Handle single request
        conn - socket connection
        addr - addr info
        f - file object to serve
        """
        #pdb.set_trace()
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
                print("%s: Seeking to %s" % (addr, seek_value))
            #send file content
            transfered = fileutils.transfer_file(conn,
                        f, progress_callback=self.send_progress_handler)
            print("%s: Bytes send %d" % (addr, transfered))
            filesize = fileutils.get_file_size(f)
            if transfered != filesize - seek_value:
                print("!! Not all data has been sent !!")
        except socket.error as e:
            print("handle_server_request error %s" % e)
        except KilledThreadException as e:
            print("Thread %s killed with message: %s" % (addr, e))
        finally:
            f.seek(0)
            f.close()
            conn.close()
            print("%s: sended urgent %s" % (addr, self._urg_sended))
            print("Client %s:%s - disconnected" % addr)

    def kill(self):
        self._killed = True


def serve_file(port, filename):
    """
    Run server on port to serve file f
    Raise exception if fails
    """
    print("Server ran...")
    server_socket = None
    threads = []
    try:
        server_socket = server.create_local_server(port)
        while(True):
            (conn, addr_info) = server_socket.accept()
            f = open(filename, "rb")
            thread = ServerThread(conn, addr_info, f)
            threads.append(thread)
            thread.start()
    except socket.error, e:
        print("Socket error: %s" % (e))
    except Exception as e:
        print("Server Exception %s" % e)
    finally:
        for thread in threads:
            if thread.is_alive():
                thread.kill()

        for thread in threads:
            thread.join()
        if server_socket:
            server_socket.close()
        print("Shutdown server")
