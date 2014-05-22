# ceph-collectd-plugin - ceph.py
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# Authors:
#   Christian Eichelmann <crapworks at gmx.net>
#
# About this plugin:
#   This plugin uses collectd's Python plugin to record ceph performances
#   data via the specified admin socket.
#
# collectd:
#   http://collectd.org
# Redis:
#   http://ceph.com
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml

import collectd
import socket
import struct
import json
import glob
import re

CEPH_ADMIN_SOCKET=''

# ceph asok format: /var/run/ceph/{cluser}-{id}.asok
ADMIN_SOCKET_REGEXP = '.*/(.+)\-(.+)\.asok$'
ADMIN_SOCKET_PATTERN = re.compile(ADMIN_SOCKET_REGEXP)

def get_cluster_name(admin_socket):
    """returns the cluster name part from admin socket"""
    m = ADMIN_SOCKET_PATTERN.match(admin_socket)
    name = None
    if m:
        name = m.group(1)
    return name
    
def get_instance_name(admin_socket):
    """returns the component (osd, mon, rgw) name part from admin socket"""
    m = ADMIN_SOCKET_PATTERN.match(admin_socket)
    name = None
    if m:
        name = m.group(2)
    return name


def query_admin_socket(admin_socket, cmd):
    """ Talk to ceph's admin socket """

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(admin_socket)
    except socket.error, e:
        collectd.error('ERROR: ceph plugin: Connecting to %s: - %r' % (admin_socket, e))
        return None
    sock.sendall(cmd)
    try:
        length = struct.unpack('>i', sock.recv(4))[0]
        json_data = json.loads(sock.recv(length))
    except Exception as err:
        collectd.error('ERROR: ceph plugin: Unable to parse json: %r' % (err, ))
        json_data = {}
    finally:
        sock.close()
        return json_data


def configure_callback(conf):
    """ Collectd configuration callback """

    global CEPH_ADMIN_SOCKET
    for node in conf.children:
        if node.key == 'AdminSocket':
            CEPH_ADMIN_SOCKET= node.values[0]
        else:
            collectd.warning('WARNING: ceph plugin: Unknown config key: %s.' % (node.key, ))


def dispatch_value(collectd_type, plugin_instance, values):
    """ Dispatch wrapper for collectd """

    cleaned_values = []

    for value in values:
        if isinstance(value, dict):
            cleaned_values.append(value['avgcount'])
        else:
            cleaned_values.append(value)

    val = collectd.Values(plugin='ceph')
    val.type = collectd_type
    val.plugin_instance = plugin_instance
    val.values = cleaned_values
    val.dispatch()


def read_callback():

    admin_sockets = glob.glob(CEPH_ADMIN_SOCKET)
    for admin_socket in admin_sockets:

        # extract instance name directly from admin_socket: /var/run/ceph/ceph-osd.25.asok -> osd.25
        plugin_instance = get_instance_name(admin_socket)
        if not plugin_instance:
            collectd.error('ERROR: ceph plugin: No name found in asok: %s' % admin_socket)
            return

        # query 'perf dump'
        perfdata = query_admin_socket(admin_socket, '{\"prefix\": \"perf dump\"}\0')
        if not perfdata:
            collectd.error('ERROR: ceph plugin: No perf data received from %s' % admin_socket)
            return

        for collectd_type, value in perfdata.iteritems():
            if not value:
                continue
            dispatch_value(collectd_type, plugin_instance, value.values())


# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
