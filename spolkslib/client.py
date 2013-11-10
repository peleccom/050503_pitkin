# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os
import fileutils


class ClientError(Exception):
    pass


class UdpClientError(Exception):
    pass


def create_client_file(filename, server_filesize, flag_overwrite=False):
    """
    Open client file in append mode or overwrite mode
    return
        (f, seek_value) if file opened
    raise ClientError n if error
    """
    seek_value = 0
    if (not flag_overwrite) and  os.path.exists(filename):
            f = open(filename, "ab")
            real_filesize = fileutils.get_file_size(f)
            if real_filesize == server_filesize:
                f.close()
                raise ClientError('File already downloaded\n'
                    'Use --overwrite flag to rewrite file')
            elif real_filesize < server_filesize:
                print(u"Appending file %s" % filename)
                f.seek(0, 2)
                seek_value = f.tell()
                print("Seek to %s" % seek_value)
            else:
                f.close()
                raise ClientError("Local file has size more than server file")
    else:
        f = open(filename, "wb")
    return (f, seek_value)
