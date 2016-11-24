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
"""Helper module for bindings that usually happen inside OSt instances"""
import pyroute2

from oslo_config import cfg

from kuryr.lib.binding.drivers import utils
from kuryr.lib import exceptions


def get_link_iface(port):
    """Gets the name of the interface to link the container virtual devices"""
    link = cfg.CONF.binding.link_iface
    if not link:
        # Guess the name from the port hwaddr
        ip = utils.get_ipdb()
        for name, data in ip.interfaces.items():
            if data['address'] == port[utils.MAC_ADDRESS_KEY]:
                link = data['ifname']
                break
    return link


def port_unbind(endpoint_id, neutron_port):
    """Unbinds the Neutron port from the network interface on the host.

    :param endpoint_id: the ID of the Docker container as string
    :param neutron_port: a port dictionary returned from python-neutronclient
    :returns: the tuple of stdout and stderr returned by processutils.execute
              invoked with the executable script for unbinding
    :raises: processutils.ProcessExecutionError, pyroute2.NetlinkError
    """
    port_id = neutron_port['id']
    _, devname = utils.get_veth_pair_names(port_id)

    try:
        utils.remove_device(devname)
    except pyroute2.NetlinkError:
        raise exceptions.VethDeletionFailure(
            'Failed to delete the container device.')

    return '', None
