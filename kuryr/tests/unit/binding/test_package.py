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

from kuryr.lib import binding
from kuryr.lib import constants
from kuryr.lib import utils
from kuryr.tests.unit import base
from mock import call

mock_create = mock.MagicMock()
mock_interface = mock.MagicMock()


@ddt.ddt
class BindingTest(base.TestCase):
    """Unit tests for binding."""

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('oslo_concurrency.processutils.execute',
                return_value=('fake_stdout', 'fake_stderr'))
    @mock.patch('pyroute2.ipdb.interface.InterfacesDict.__getattribute__',
                return_value=mock_create)
    @mock.patch('pyroute2.ipdb.interface.InterfacesDict.__getitem__',
                return_value=mock_interface)
    def test_port_bind(self, mock_getitem, mock_getattribute,
                       mock_execute, mock_path_exists):
        fake_mtu = 1450
        fake_docker_network_id = utils.get_hash()
        fake_docker_endpoint_id = utils.get_hash()
        fake_port_id = uuidutils.generate_uuid()
        fake_neutron_v4_subnet_id = uuidutils.generate_uuid()
        fake_neutron_v6_subnet_id = uuidutils.generate_uuid()
        fake_port = self._get_fake_port(
            fake_docker_endpoint_id, fake_docker_network_id,
            fake_port_id, constants.PORT_STATUS_ACTIVE,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        fake_subnets = self._get_fake_subnets(
            fake_docker_endpoint_id, fake_docker_network_id,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        fake_network = self._get_fake_networks(fake_docker_network_id)
        fake_network['networks'][0]['mtu'] = fake_mtu

        binding.port_bind(fake_docker_endpoint_id, fake_port['port'],
                          fake_subnets['subnets'],
                          fake_network['networks'][0])

        expect_calls = [call.__enter__().set_mtu(fake_mtu),
                        call.__enter__().up()]
        mock_interface.assert_has_calls(expect_calls, any_order=True)
        mock_path_exists.assert_called_once()
        mock_execute.assert_called_once()

    @mock.patch('kuryr.lib.binding.drivers.utils.remove_device')
    @mock.patch('oslo_concurrency.processutils.execute',
                return_value=('fake_stdout', 'fake_stderr'))
    def test_port_unbind(self, mock_execute, mock_remove_device):
        fake_docker_network_id = utils.get_hash()
        fake_docker_endpoint_id = utils.get_hash()
        fake_port_id = uuidutils.generate_uuid()
        fake_neutron_v4_subnet_id = uuidutils.generate_uuid()
        fake_neutron_v6_subnet_id = uuidutils.generate_uuid()
        fake_port = self._get_fake_port(
            fake_docker_endpoint_id, fake_docker_network_id,
            fake_port_id, constants.PORT_STATUS_ACTIVE,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        binding.port_unbind(fake_docker_endpoint_id, fake_port['port'])
        mock_execute.assert_called_once()
        mock_remove_device.assert_called_once()
