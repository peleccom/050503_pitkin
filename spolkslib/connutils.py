# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os


def send_buffer(conn, buffer):
    """
    Send a buffer content through socket (conn)
    return true if successfull
    """
    try:
        need_send = len(buffer)
        bytes_sended = conn.send(buffer)
        while (bytes_sended < need_send):
            buffer = buffer[bytes_sended:]
            need_send = len(buffer)
            bytes_sended = conn.send(buffer)
        return True
    except Exception as e:
        print("send_buffer error %s" % e)
        return False


def recv_buffer(conn, buffer_size):
    """
    Recieve buffer from a network connection
    buffer_sizse - buffer length
    conn - socket
    return buffer, buffer size can be less than buffer_size value\
    if can't receive more data
    """
    buffer = ''
    readed = 0
    try:
        while(True):
            if readed == buffer_size:
                break
            chunk = conn.recv(buffer_size - readed)
            if not len(chunk):
                break
            readed += len(chunk)
            buffer += chunk
    except socket.error as e:
        print("recv_buffer error %s" % e)
    return buffer
