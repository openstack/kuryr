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

from oslo_concurrency import processutils

from kuryr.lib.binding.drivers import utils
from kuryr.lib import constants


def port_bind(endpoint_id, port, subnets, network=None, vm_port=None,
              segmentation_id=None, **kwargs):
    """Binds the Neutron port to the network interface on the host.

    :param endpoint_id:   the ID of the endpoint as string
    :param port:         the container Neutron port dictionary as returned by
                         python-neutronclient
    :param subnets:      an iterable of all the Neutron subnets which the
                         endpoint is trying to join
    :param network:      the Neutron network which the endpoint is trying to
                         join
    :param vm_port:      the Nova instance port dictionary, as returned by
                         python-neutronclient. Container port under binding is
                         running inside this instance (either ipvlan/macvlan or
                         a subport)
    :param segmentation_id: ID of the segment for container traffic isolation)
    :param kwargs:       Additional driver-specific arguments
    :returns: the tuple of the names of the veth pair and the tuple of stdout
              and stderr returned by processutils.execute invoked with the
              executable script for binding
    :raises: kuryr.common.exceptions.VethCreationFailure,
             processutils.ProcessExecutionError
    """
    pf_ifname = kwargs['pf_ifname']
    vf_num = kwargs['vf_num']
    mac_addr = port[utils.MAC_ADDRESS_KEY]
    vlan = port[constants.VIF_DETAILS_KEY][constants.VIF_DETAILS_VLAN_KEY]
    _set_vf_interface_vlan(pf_ifname, vf_num, mac_addr, vlan)
    return None, None, ('', None)


def port_unbind(endpoint_id, neutron_port, **kwargs):
    """Unbinds the Neutron port from the network interface on the host.

    :param endpoint_id: the ID of the Docker container as string
    :param neutron_port: a port dictionary returned from python-neutronclient
    :param kwargs:       Additional driver-specific arguments
    :returns: the tuple of stdout and stderr returned by processutils.execute
              invoked with the executable script for unbinding
    :raises: processutils.ProcessExecutionError, pyroute2.NetlinkError
    """
    pf_ifname = kwargs['pf_ifname']
    vf_num = kwargs['vf_num']
    mac_addr = neutron_port[utils.MAC_ADDRESS_KEY]
    _set_vf_interface_vlan(pf_ifname, vf_num, mac_addr)
    return '', None


def _set_vf_interface_vlan(pf_ifname, vf_num, mac_addr, vlan=0):
    exit_code = [0, 2, 254]
    processutils.execute('ip', 'link', 'set', pf_ifname,
                         'vf', vf_num,
                         'mac', mac_addr,
                         'vlan', vlan,
                         check_exit_code=exit_code)
