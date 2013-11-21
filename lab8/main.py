#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
from __future__ import print_function
import sys
import argparse
import os

# A liitle hack to load lib from top-level
if __name__ == '__main__':
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lab5 import client_udp
from lab5 import server_udp
from lab4 import client_tcp
import server_common


def server_command(args):
    if not os.path.isfile(args.r):
        print("File %s doesn't exists" % args.r)
        sys.exit(1)
    try:
        server_common.serve_file(args.port, args.r)
    except Exception, e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt as e:
        print("Server interruped by user")
        sys.exit(1)


def client_command(args):
    try:
        if args.udp:
            client_udp.get_file_from_server(args.host, args.port,
                args.w, args.overwrite)
        else:
            client_tcp.get_file_from_server(args.host, args.port,
                args.w, args.overwrite)
    except KeyboardInterrupt as e:
        print("Client interrupted")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Select mode')
    parser_server = subparsers.add_parser("server", help="Run as server")
    parser_client = subparsers.add_parser("client", help="Run as client")
    parser_server.add_argument("port", type=int)
    parser_server.add_argument("-r", help="Filename to read from",
        required=True, metavar="filename")
    parser_server.set_defaults(func=server_command)
    parser_client.add_argument("host")
    parser_client.add_argument("port", type=int)
    parser_client.add_argument("-u", "--udp",
        help="Use UDP connection", action="store_true")
    parser_client.add_argument("-w", help="Filename to write",
        required=True, metavar="filename ")
    parser_client.add_argument("-o", "--overwrite",
        help="Rewrite file if exists", action="store_true")
    parser_client.set_defaults(func=client_command)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
