# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os

BUFFER_SIZE = 1024


def get_file_size(f):
    '''Return file-like object file size'''
    f.seek(0, 2)
    size = f.tell()
    f.seek(0, 0)
    return size


def transfer_file(sock, f, buf_size=BUFFER_SIZE):
    '''Transfer file-like object (f) through socket (sock)'''
    total_bytes_sended = 0
    while True:
        buffer = f.read(buf_size)
        need_send = len(buffer)
        if not need_send:
            break
        bytes_sended = sock.send(buffer)
        total_bytes_sended += bytes_sended
        while (bytes_sended < need_send):
            buffer = buffer[bytes_send:]
            need_send = len(buffer)
            bytes_sended = sock.send(buffer)
            total_bytes_sended += bytes_sended
    return total_bytes_sended


def recv_file(sock, f, filesize,  buf_size=BUFFER_SIZE):
    '''Receive file from socket'''
    total_bytes_readed = 0
    while (True):
        if total_bytes_readed == filesize:
            break
        buffer = sock.recv(buf_size)
        bytes_readed = len(buffer)
        total_bytes_readed += bytes_readed
        if not bytes_readed:
            break
        f.write(buffer)
    return total_bytes_readed
