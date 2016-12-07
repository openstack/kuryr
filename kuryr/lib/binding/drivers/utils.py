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
import ipaddress

import pyroute2
from pyroute2.netlink.rtnl import ifinfmsg
import six

from kuryr.lib import constants


_IPDB_CACHE = None

FIXED_IP_KEY = 'fixed_ips'
IP_ADDRESS_KEY = 'ip_address'
MAC_ADDRESS_KEY = 'mac_address'
SUBNET_ID_KEY = 'subnet_id'


def get_veth_pair_names(port_id):
    ifname = constants.VETH_PREFIX + port_id
    ifname = ifname[:constants.NIC_NAME_LEN]
    peer_name = constants.CONTAINER_VETH_PREFIX + port_id
    peer_name = peer_name[:constants.NIC_NAME_LEN]
    return ifname, peer_name


def get_ipdb():
    """Returns the already cached or a newly created IPDB instance.

    IPDB reads the Linux specific file when it's instantiated. This behaviour
    prevents Mac OSX users from running unit tests. This function makes the
    loading IPDB lazyily and therefore it can be mocked after the import of
    modules that import this module.

    :returns: The already cached or newly created ``pyroute2.IPDB`` instance
    """
    global _IPDB_CACHE
    if not _IPDB_CACHE:
        _IPDB_CACHE = pyroute2.IPDB()
    return _IPDB_CACHE


def get_mtu_from_network(network=None):
    """Get Maximum Transfer Unit from neutron network.

    :parm network: neutron network
    :returns: mtu on the neutron network
    """
    if network is None:
        mtu = constants.DEFAULT_NETWORK_MTU
    else:
        mtu = network.get('mtu', constants.DEFAULT_NETWORK_MTU)
    return mtu


def remove_device(ifname):
    """Removes the device with name ifname.

    :param ifname: the name of the device to remove
    :returns: the index the device identified by ifname had if it
              exists, otherwise None
    :raises: pyroute2.NetlinkError
    """
    ip = get_ipdb()

    dev_index = ip.interfaces.get(ifname, {}).get('index', None)

    if dev_index:
        with ip.interfaces[ifname] as iface:
            iface.remove()

    return dev_index


def is_up(interface):
    flags = interface['flags']
    if not flags:
        return False
    return (flags & ifinfmsg.IFF_UP) == 1


def _configure_container_iface(iface, subnets, fixed_ips, mtu=None,
                               hwaddr=None):
    """Configures the interface that is placed in the container net ns

    :param iface:       the pyroute IPDB interface object to configure
    :param subnets:     an iterable of all the Neutron subnets which the
                        endpoint is trying to join
    :param fixed_ips:   an iterable of fixed IPs to be set for the iface
    :param mtu:         Maximum Transfer Unit to set for the iface
    :param hwaddr:      Hardware address to set for the iface
    """
    subnets_dict = {subnet['id']: subnet for subnet in subnets}
    # We assume containers always work with fixed ips, dhcp does not really
    # make a lot of sense
    for fixed_ip in fixed_ips:
        if IP_ADDRESS_KEY in fixed_ip and (SUBNET_ID_KEY in fixed_ip):
            subnet_id = fixed_ip[SUBNET_ID_KEY]
            subnet = subnets_dict[subnet_id]
            cidr = ipaddress.ip_network(six.text_type(subnet['cidr']))
            iface.add_ip(fixed_ip[IP_ADDRESS_KEY], cidr.prefixlen)
    if mtu is not None:
        iface.set_mtu(mtu)
    if hwaddr is not None:
        iface.set_address(hwaddr)
    if not is_up(iface):
        iface.up()
