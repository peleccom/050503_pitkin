# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os

import connutils
from protocol import MyCommandProtocol
import protocol

BUFFER_SIZE = 1024


def get_file_size(f):
    """Return a file size of file-like object """
    old_position = f.tell()
    f.seek(0, 2)
    size = f.tell()
    f.seek(old_position, 0)
    return size


def transfer_file(sock, f, buf_size=BUFFER_SIZE, progress_callback=None):
    """
    Transfer file-like object (f) through socket (sock)
    progress_callback - callback function, called when a packet of
        data send.
        def progress_handler(sock, count)
    """
    total_bytes_sended = 0
    while True:
        buffer = f.read(buf_size)
        need_send = len(buffer)
        if not need_send:
            break
        if not connutils.send_buffer(sock, buffer):
            break
        total_bytes_sended += need_send
        #call callback
        if progress_callback and hasattr(progress_callback, "__call__"):
            progress_callback(sock, total_bytes_sended)
    return total_bytes_sended


def recv_file(sock, f, download_limit, buf_size=BUFFER_SIZE,
                progress_callback=None):
    """
    Receive file from socket
    sock - socket
    f - file-like object
    download_limit - reeiving file size
    buf_size - receive buffer size
    progress_callback - callback function, called when a packet of
        data received.
        def progress_handler(sock, count)
    Return a count of received bytes
    """
    total_bytes_received = 0
    while (True):
        need_download = (download_limit - total_bytes_received)

        buffer = connutils.recv_buffer(sock, min(need_download, buf_size))
        bytes_readed = len(buffer)
        if buffer:
            f.write(buffer)
            total_bytes_received += bytes_readed
            #Run callback
            if (progress_callback
                and hasattr(progress_callback, "__call__")):
                progress_callback(sock, total_bytes_received)
        if ((total_bytes_received == download_limit) or
            (bytes_readed < buf_size)):
            break
    return total_bytes_received


def recv_file_udp(sock, f, download_limit, myDatagram, buf_size=BUFFER_SIZE,
                progress_callback=None):
    """
    Receive file from socket
    sock - socket
    f - file-like object
    download_limit - reeiving file size
    buf_size - receive buffer size
    progress_callback - callback function, called when a packet of
        data received.
        def progress_handler(sock, count)
    Return a count of received bytes
    """
    total_bytes_received = 0
    while (True):
        need_download = (download_limit - total_bytes_received)
        recv_data_size = min(need_download, buf_size)
        buffer = myDatagram.send_request_blocking(sock,
                protocol.PROTOCOL_COMMAND_SEEK, f.tell(),
                recv_data_size=recv_data_size)

        # file content in buffer

        if buffer:
            bytes_readed = len(buffer)
            f.write(buffer)
            total_bytes_received += bytes_readed
            #Run callback
            if (progress_callback
                and hasattr(progress_callback, "__call__")):
                progress_callback(sock, total_bytes_received)
        else:
            bytes_readed = 0
        if ((total_bytes_received == download_limit) or
            (bytes_readed < buf_size)):
            break
    return total_bytes_received
