# -*- coding: UTF-8 -*-
from __future__ import print_function
import socket
import os

import connutils
import fileutils
import client
import struct



PROTOCOL_COMMAND_SEEK = 'SEEK' # request chunk at
PROTOCOL_COMMAND_DATA = 'DATA' # response with chunk
PROTOCOL_COMMAND_SIZE = 'SIZE' # request file size
PROTOCOL_COMMAND_FILE = 'FILE' # response with file size
BUFFER_SIZE = 1024
#
class ProtocolError(Exception):
    pass
#
class CommandProtocolException(Exception):
    pass

class MyDatagram(object):
    def __init__(self, server=False):
        """
        Create new client object
        if server = True - create server object
        """
        self._datagram_number = 0
        self._server = server

    def get_datagram_number(self):
        return self._datagram_number

    def pack(self, data, datagram_number = None):
        if datagram_number == None:
            if self._server:
                datagram_number = self._datagram_number
            else:
                datagram_number = self._datagram_number + 1
        self._datagram_number = datagram_number
        buffer = data + struct.pack("!I", datagram_number)
        return buffer

    def unpack(self, datagram):
        size = len(datagram)
        if size <=4:
            raise ProtocolError("Invalid size")
        actual_size = size - 4
        number_field = struct.unpack("!I", datagram[-4:])
        if not number_field:
            raise ProtocolError("Invalid datagarm number")
        if self._server:
            self._datagram_number = number_field[0]
        buffer = datagram[:-4]
        res = {
                'data': buffer,
                'datagram_number': number_field[0]
              }
        return res

    def calculate_datagram_size(self, buffer_size):
        return buffer_size + 4

    def send_request_blocking(self, sock, command_type, *args, **kwargs):
        """
        Send command
        Return answer if successtype
        """
        recv_buffer_size = 0
        #make request structure

        if command_type == PROTOCOL_COMMAND_SIZE:
            # send size command
            command = MyCommandProtocol.size_request(*args)
            recv_buffer_size = self.calculate_datagram_size(
                            MyCommandProtocol.SIZE_COMMAND_FILE)
        elif command_type == PROTOCOL_COMMAND_SEEK:
            recv_data_size = kwargs['recv_data_size']
            command = MyCommandProtocol.seek_request(*args)
            recv_buffer_size = self.calculate_datagram_size(
                        MyCommandProtocol.SIZE_COMMAND_DATA + recv_data_size)
        else:
            raise CommandProtocolException("Invalid command")
        buffer = self.pack(command)
        connutils.send_buffer(sock, buffer)
        buffer = connutils.recv_buffer(sock, recv_buffer_size)
        datagram_dict = self.unpack(buffer)
        command = datagram_dict['data']
        # extract and return result
        if command_type == PROTOCOL_COMMAND_SIZE:
            filesize = MyCommandProtocol.unpack_file_command(command)
            return filesize
        elif command_type == PROTOCOL_COMMAND_SEEK:
            data = MyCommandProtocol.unpack_data_command(command)
            return data


class MyCommandProtocol(object):
    PROTOCOL_COMMAND_RECORD_SIZE = 12
    SIZE_COMMAND_FILE = 4 + 8
    SIZE_COMMAND_SEEK = 4 + 8
    SIZE_COMMAND_DATA = 4
    SIZE_COMMAND_SIZE = 4 + 8 # must be equal to size of SEEK_COMMAND


    @staticmethod
    def size_request():
        buffer = PROTOCOL_COMMAND_SIZE + ' ' * 8
        return buffer

    @staticmethod
    def seek_request(seek_value):
        buffer = PROTOCOL_COMMAND_SEEK + struct.pack("!Q", seek_value)
        return buffer

    @staticmethod
    def size_response(size):
        buffer = PROTOCOL_COMMAND_FILE + struct.pack("!Q", size)
        return buffer

    @staticmethod
    def data_response(data):
        return PROTOCOL_COMMAND_DATA + data

    @staticmethod
    def recognize_command(buffer):
        command = buffer[:4]
        if not command in  (PROTOCOL_COMMAND_DATA, PROTOCOL_COMMAND_FILE,
                            PROTOCOL_COMMAND_SEEK, PROTOCOL_COMMAND_SIZE):
            raise CommandProtocolException("Invalid command")
        return command

    @staticmethod
    def unpack_size_command(buffer):
        command = MyCommandProtocol.recognize_command(buffer)
        if command != PROTOCOL_COMMAND_SIZE:
            raise CommandProtocolException('Not SIZE command')

    @staticmethod
    def unpack_seek_command(buffer):
        command = MyCommandProtocol.recognize_command(buffer)
        if command != PROTOCOL_COMMAND_SEEK:
            raise CommandProtocolException('Not SEEK command')
        seek_value =  struct.unpack("!Q", buffer[4:])
        if seek_value:
            return int(seek_value[0])
        raise CommandProtocolException('Invalid SEEK value')

    @staticmethod
    def unpack_file_command(buffer):
        command = MyCommandProtocol.recognize_command(buffer)
        if command != PROTOCOL_COMMAND_FILE:
            raise CommandProtocolException('Not FILE command')
        size_value =  struct.unpack("!Q", buffer[4:])
        if size_value and size_value[0]:
            return size_value[0]
        raise CommandProtocolException('Invalid SIZE value')

    @staticmethod
    def unpack_data_command(buffer):
        command = MyCommandProtocol.recognize_command(buffer)
        if command != PROTOCOL_COMMAND_DATA:
            raise CommandProtocolException('Not DATA command')
        return buffer[4:]