#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import ddt
import mock
from oslo_utils import uuidutils

import pyroute2.ipdb.interface
from pyroute2.netlink.rtnl import ifinfmsg

from kuryr.lib.binding.drivers import utils
from kuryr.lib import constants
from kuryr.tests.unit import base


@ddt.ddt
class BindingDriversUtilsTest(base.TestCase):
    """Unit tests for binding drivers utils"""

    def test_get_veth_pair_names(self):
        fake_neutron_port_id = uuidutils.generate_uuid()
        generated_ifname, generated_peer = utils.get_veth_pair_names(
            fake_neutron_port_id)

        namelen = constants.NIC_NAME_LEN
        ifname_postlen = namelen - len(constants.VETH_PREFIX)
        peer_postlen = namelen - len(constants.CONTAINER_VETH_PREFIX)

        self.assertEqual(namelen, len(generated_ifname))
        self.assertEqual(namelen, len(generated_peer))
        self.assertIn(constants.VETH_PREFIX, generated_ifname)
        self.assertIn(constants.CONTAINER_VETH_PREFIX, generated_peer)
        self.assertIn(fake_neutron_port_id[:ifname_postlen], generated_ifname)
        self.assertIn(fake_neutron_port_id[:peer_postlen], generated_peer)

    @ddt.data((False), (True))
    def test_is_up(self, interface_flag):
        fake_interface = {'flags': 0x0}
        if interface_flag:
            fake_interface['flags'] = ifinfmsg.IFF_UP
            self.assertEqual(True, utils.is_up(fake_interface))
        else:
            self.assertEqual(False, utils.is_up(fake_interface))

    @ddt.data(
        (['10.10.10.11'], ['384ac9fc-eefa-4399-8d88-1181433e33b1'], False,
         None, None),
        (['10.10.10.11'], ['384ac9fc-eefa-4399-8d88-1181433e33b1'],
         True, None, None),
        (['10.10.10.11', '10.11.0.10'],
         ['384ac9fc-eefa-4399-8d88-1181433e33b1',
          '0a6eab28-9dc1-46c0-997c-cb9f66f6081f'],
         False, 1500, 'fa:16:3e:22:a3:3d'))
    @ddt.unpack
    @mock.patch.object(utils, 'is_up')
    def test__configure_container_iface(
            self, addrs, subnet_ids, already_up, mtu, mac, mock_is_up):
        subnets = [{
            'allocation_pools': [{'end': '10.11.0.254', 'start': '10.11.0.2'}],
            'cidr': '10.11.0.0/26',
            'created_at': '2016-09-27T07:55:12',
            'description': '',
            'dns_nameservers': [],
            'enable_dhcp': True,
            'gateway_ip': '10.11.0.1',
            'host_routes': [],
            'id': '0a6eab28-9dc1-46c0-997c-cb9f66f6081f',
            'ip_version': 4,
            'ipv6_address_mode': None,
            'ipv6_ra_mode': None,
            'name': 'subtest',
            'network_id': '90146ed2-c3ce-4001-866e-e97e513530a3',
            'revision': 2,
            'service_types': [],
            'subnetpool_id': None,
            'tenant_id': '0c0d1f46fa8d485d9534ea0e35f37bd3',
            'updated_at': '2016-09-27T07:55:12'
        }, {
            'allocation_pools': [{'end': '10.10.0.254', 'start': '10.10.0.2'}],
            'cidr': '10.10.0.0/24',
            'created_at': '2016-09-27T08:57:13',
            'description': '',
            'dns_nameservers': [],
            'enable_dhcp': True,
            'gateway_ip': '10.10.0.1',
            'host_routes': [],
            'id': '384ac9fc-eefa-4399-8d88-1181433e33b1',
            'ip_version': 4,
            'ipv6_address_mode': None,
            'ipv6_ra_mode': None,
            'name': '10.10.0.0/24',
            'network_id': 'bfb2f525-bedf-48ed-b125-102ee7920253',
            'revision': 2,
            'service_types': [],
            'subnetpool_id': None,
            'tenant_id': '51b66b97a12f42a990452967d2c555ac',
            'updated_at': '2016-09-27T08:57:13'}]

        fake_iface = mock.Mock(spec=pyroute2.ipdb.interface.Interface)
        _set_mtu = mock.Mock()
        _set_address = mock.Mock()
        fake_iface.attach_mock(_set_mtu, 'set_mtu')
        fake_iface.attach_mock(_set_address, 'set_address')
        mock_is_up.return_value = already_up

        fixed_ips = []
        for ip, subnet_id in zip(addrs, subnet_ids):
            fixed_ips.append({
                utils.IP_ADDRESS_KEY: ip,
                utils.SUBNET_ID_KEY: subnet_id})

        utils._configure_container_iface(
            fake_iface,
            subnets,
            fixed_ips,
            mtu=mtu,
            hwaddr=mac)

        subnets_prefix_by_id = dict(
            (subnet['id'], int(subnet['cidr'].split('/')[1])) for
            subnet in subnets)
        for ip, subnet_id in zip(addrs, subnet_ids):
            fake_iface.add_ip.assert_any_call(
                ip, subnets_prefix_by_id[subnet_id])

        if already_up:
            fake_iface.up.assert_not_called()
        else:
            fake_iface.up.assert_called_once()

        if mtu is None:
            fake_iface.set_mtu.assert_not_called()
        else:
            fake_iface.set_mtu.assert_called_with(mtu)

        if mac is None:
            fake_iface.set_address.assert_not_called()
        else:
            fake_iface.set_address.assert_called_with(mac)

    def test_get_ipdb(self):
        ip = utils.get_ipdb()
        self.assertEqual(ip, utils.get_ipdb())
