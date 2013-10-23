# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os


def create_local_server(port, use_UDP=False, backlog=1):
    """
    Create TCP(UDP) server at specified port
    Raise ValueError at wrong port value
    Can raise socket_error ValueError
    """
    if not 0 <= port <= 65535:
        raise ValueError("port must be 0-65535")
    if not use_UDP:
        socket_type = socket.SOCK_STREAM
    else:
        socket_type = socket.SOCK_DGRAM
    s = socket.socket(socket.AF_INET, socket_type)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    if not use_UDP:
        s.listen(backlog)
    return s
