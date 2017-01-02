# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import hashlib
import random
import socket

from keystoneauth1 import loading as ks_loading
from neutronclient.v2_0 import client
from oslo_config import cfg

from kuryr.lib import config as kuryr_config

DOCKER_NETNS_BASE = '/var/run/docker/netns'
PORT_POSTFIX = 'port'


def get_auth_plugin(conf_group):
    return ks_loading.load_auth_from_conf_options(
        cfg.CONF, conf_group)


def get_keystone_session(conf_group, auth_plugin):
    return ks_loading.load_session_from_conf_options(cfg.CONF,
                                                     conf_group,
                                                     auth=auth_plugin)


def get_neutron_client(*args, **kwargs):
    conf_group = kuryr_config.neutron_group.name
    auth_plugin = get_auth_plugin(conf_group)
    session = get_keystone_session(conf_group, auth_plugin)
    endpoint_type = getattr(getattr(cfg.CONF, conf_group), 'endpoint_type')

    return client.Client(session=session,
                         auth=auth_plugin,
                         endpoint_type=endpoint_type)


def get_hostname():
    """Returns the host name."""
    return socket.gethostname()


def get_neutron_subnetpool_name(subnet_cidr):
    """Returns a Neutron subnetpool name.

    :param subnet_cidr: The subnetpool allocation cidr
    :returns: the Neutron subnetpool_name name formatted appropriately
    """
    name_prefix = cfg.CONF.subnetpool_name_prefix
    return '-'.join([name_prefix, subnet_cidr])


def get_dict_format_fixed_ips_from_kv_format(fixed_ips):
    """Returns fixed_ips in dict format.

    :param fixed_ips: Format that neutron client expects for list_ports ex,
                      ['subnet_id=5083bda8-1b7c-4625-97f3-1d4c33bfeea8',
                       'ip_address=192.168.1.2']
    :returns: normal dict form,
              [{'subnet_id': '5083bda8-1b7c-4625-97f3-1d4c33bfeea8',
                'ip_address': '192.168.1.2'}]
    """
    new_fixed_ips = []
    for fixed_ip in fixed_ips:
        if 'subnet_id' == fixed_ip.split('=')[0]:
            subnet_id = fixed_ip.split('=')[1]
        else:
            ip = fixed_ip.split('=')[1]
            new_fixed_ips.append({'subnet_id': subnet_id,
                'ip_address': ip})
    return new_fixed_ips


def getrandbits(bit_size=256):
    return str(random.getrandbits(bit_size)).encode('utf-8')


def get_hash(bit_size=256):
    return hashlib.sha256(getrandbits(bit_size=bit_size)).hexdigest()


def string_mappings(mapping_list):
    """Make a string out of the mapping list"""
    details = ''
    if mapping_list:
        details = '"' + str(mapping_list) + '"'
        return details


def get_random_string(length):
    """Get a random hex string of the specified length."""

    return "{0:0{1}x}".format(random.getrandbits(length * 4), length)
