#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import socket
import struct
import json

class CephAdminSocketError(Exception):
    pass

class CollectdTypesDB(object):
    def __init__(self, adminsocket):
        self.adminsocket = adminsocket

    def _get_schema(self):
        """Connect to ceph admin socket and request performance schema"""

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.adminsocket)
        except socket.error as err:
            raise CephAdminSocketError('Error connecting to ceph admin socket %s: - %r' % (self.adminsocket, err))

        sock.sendall('{\"prefix\": \"perf schema\"}\0')

        try:
            length = struct.unpack('>i', sock.recv(4))[0]
            json_data = json.loads(sock.recv(length))
            return json_data
        except Exception as err:
            raise CephAdminSocketError('unable to parse json: %r' % (err, ))
        finally:
            sock.close()

    def ceph2collectd(self, type_num):
        if 8 & type_num:
            return 'COUNTER'
        else:
            return 'GAUGE'

    def __str__(self):
        tmp = ''

        for plugin_instance, collectd_types in self._get_schema().iteritems():
            if not collectd_types:
                continue

            for name, type_num in collectd_types.iteritems():
                data = 'value:%s:U:U' % (self.ceph2collectd(type_num['type']))
                tmp += '%s_%s %s\n' % (name, plugin_instance, data)

        return tmp

def main():
    if len(sys.argv) < 2:
        print "[-] usage: %s <ceph admin socket>" % (sys.argv[0], )
    else:
        try:
            typesdb = CollectdTypesDB(sys.argv[1])
            print typesdb
        except CephAdminSocketError as err:
            print "[-] error: %s" % (str(err), )

if __name__ == '__main__':
    main()
