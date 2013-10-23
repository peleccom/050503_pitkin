# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os

import connutils

BUFFER_SIZE = 1024


def get_file_size(f):
    """Return file-like object file size"""
    f.seek(0, 2)
    size = f.tell()
    f.seek(0, 0)
    return size


def transfer_file(sock, f, buf_size=BUFFER_SIZE):
    """Transfer file-like object (f) through socket (sock)"""
    total_bytes_sended = 0
    while True:
        buffer = f.read(buf_size)
        need_send = len(buffer)
        if not need_send:
            break
        if not connutils.send_buffer(sock, buffer):
            break
        total_bytes_sended += need_send
    return total_bytes_sended


def recv_file(sock, f, download_limit,  buf_size=BUFFER_SIZE):
    """
    Receive file from socket
    Return count of bytes received
    """
    total_bytes_readed = 0
    while (True):
        need_download = (download_limit - total_bytes_readed)
        if need_download > buf_size:
            buffer = connutils.recv_buffer(sock, buf_size)
        else:
            buffer = connutils.recv_buffer(sock, need_download)
        bytes_readed = len(buffer)
        if buffer:
            f.write(buffer)
            total_bytes_readed += bytes_readed
        if ((total_bytes_readed == download_limit) or
            (bytes_readed < BUFFER_SIZE)):
            break
    return total_bytes_readed
