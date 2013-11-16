# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os
import trace
import time


URGENT_BYTE = "!"


def _universal_send_buffer(conn, buffer, udp_addr=None):
    """Use send_buffer and send_buffer_to instead"""
    try:
        need_send = len(buffer)
        if not udp_addr:
            bytes_sended = conn.send(buffer)
        else:
            bytes_sended = conn.sendto(buffer, udp_addr)
        time.sleep(0.001)
        while (bytes_sended < need_send):
            buffer = buffer[bytes_sended:]
            need_send = len(buffer)
            if not udp_addr:
                bytes_sended = conn.send(buffer)
            else:
                bytes_sended = conn.sendto(buffer, udp_addr)
        return True
    except Exception as e:
        print("send_buffer error %s" % e)
        return False


def _universal_recv_buffer(conn, buffer_size, udp=None):
    """Use recv_buffer and recv_buffer_from intead"""
    buffer = ''
    readed = 0
    try:
        while(True):
            if readed == buffer_size:
                break
            if not udp:
                chunk = conn.recv(buffer_size - readed)
            else:
                (chunk, addr) = conn.recvfrom(buffer_size - readed)
            time.sleep(0.001)
            if not len(chunk):
                break
            readed += len(chunk)
            buffer += chunk
    except socket.error as e:
        print("recv_buffer error %s" % e)
    if not udp:
        return buffer
    else:
        return (buffer, addr)


def send_buffer_to(conn, buffer, addr):
    """
    Send a buffer content through socket (conn) to address (addr)
    return true if successfull
    """
    return _universal_send_buffer(conn, buffer, addr)


def recv_buffer_from(conn, buffer_size):
    """
    Recieve buffer from a udp network connection
    buffer_size - buffer length
    conn - socket
    return (buffer ,addr) , buffer size can be less than buffer_size value\
    if can't receive more data
    """
    return _universal_recv_buffer(conn, buffer_size, True)


def send_buffer(conn, buffer):
    """
    Send a buffer content through socket (conn)
    return true if successfull
    """
    return _universal_send_buffer(conn, buffer)


def recv_buffer(conn, buffer_size):
    """
    Recieve buffer from a network connection
    buffer_size - buffer length
    conn - socket
    return buffer, buffer size can be less than buffer_size value\
    if can't receive more data
    """
    return _universal_recv_buffer(conn, buffer_size)
