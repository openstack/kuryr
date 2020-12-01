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


from unittest import mock

from oslo_utils import uuidutils

from kuryr.lib.binding.drivers import hw_veb
from kuryr.lib import constants
from kuryr.lib import utils
from kuryr.tests.unit import base


mock_create = mock.MagicMock()
mock_interface = mock.MagicMock()


class TestHwVebDriver(base.TestCase):
    """Unit tests for hw_veb driver"""

    @mock.patch('oslo_concurrency.processutils.execute',
                return_value=('fake_stdout', 'fake_stderr'))
    def test_port_bind(self, mock_execute):
        fake_docker_endpoint_id = utils.get_hash()
        fake_docker_network_id = utils.get_hash()
        fake_port_id = uuidutils.generate_uuid()
        fake_neutron_v4_subnet_id = uuidutils.generate_uuid()
        fake_neutron_v6_subnet_id = uuidutils.generate_uuid()
        fake_vlan_id = 100
        fake_vif_details = {constants.VIF_DETAILS_VLAN_KEY: fake_vlan_id}
        fake_vif_type = "ovs"
        fake_port = self._get_fake_port(
            fake_docker_endpoint_id, fake_docker_network_id,
            fake_port_id, constants.PORT_STATUS_ACTIVE,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id,
            vif_details=fake_vif_details, vif_type=fake_vif_type)
        fake_subnets = self._get_fake_subnets(
            fake_docker_endpoint_id, fake_docker_network_id,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        fake_network = self._get_fake_networks(fake_docker_network_id)
        fake_pf_ifname = 'eth13'
        fake_vf_num = 1

        hw_veb.port_bind(fake_docker_endpoint_id,
                         fake_port['port'],
                         fake_subnets['subnets'],
                         fake_network['networks'][0],
                         pf_ifname=fake_pf_ifname,
                         vf_num=fake_vf_num)

        mock_execute.assert_called_once_with(
            'ip', 'link', 'set', fake_pf_ifname,
            'vf', fake_vf_num,
            'mac', fake_port['port']['mac_address'],
            'vlan', fake_vlan_id,
            check_exit_code=[0, 2, 254])

    @mock.patch('oslo_concurrency.processutils.execute',
                return_value=('fake_stdout', 'fake_stderr'))
    def test_port_unbind(self, mock_execute):
        fake_docker_endpoint_id = utils.get_hash()
        fake_docker_network_id = utils.get_hash()
        fake_port_id = uuidutils.generate_uuid()
        fake_neutron_v4_subnet_id = uuidutils.generate_uuid()
        fake_neutron_v6_subnet_id = uuidutils.generate_uuid()
        fake_vif_type = "ovs"
        fake_port = self._get_fake_port(
            fake_docker_endpoint_id, fake_docker_network_id,
            fake_port_id, constants.PORT_STATUS_ACTIVE,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id,
            vif_type=fake_vif_type)
        fake_pf_ifname = 'eth13'
        fake_vf_num = 1
        hw_veb.port_unbind(fake_docker_endpoint_id, fake_port['port'],
                           pf_ifname=fake_pf_ifname,
                           vf_num=fake_vf_num)
        mock_execute.assert_called_once()
        mock_execute.assert_called_once_with(
            'ip', 'link', 'set', fake_pf_ifname,
            'vf', fake_vf_num,
            'mac', fake_port['port']['mac_address'],
            'vlan', 0,
            check_exit_code=[0, 2, 254])
