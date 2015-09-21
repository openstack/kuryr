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
import uuid

import ddt
from oslo_serialization import jsonutils

from kuryr import app
from kuryr.common import constants
from kuryr.tests import base
from kuryr import utils


@ddt.ddt
class TestKuryr(base.TestKuryrBase):
    """Basic unitests for libnetwork remote driver URI endpoints.

    This test class covers the following HTTP methods and URIs as described in
    the remote driver specification as below:

      https://github.com/docker/libnetwork/blob/3c8e06bc0580a2a1b2440fe0792fbfcd43a9feca/docs/remote.md  # noqa

    - POST /Plugin.Activate
    - POST /NetworkDriver.CreateNetwork
    - POST /NetworkDriver.DeleteNetwork
    - POST /NetworkDriver.CreateEndpoint
    - POST /NetworkDriver.EndpointOperInfo
    - POST /NetworkDriver.DeleteEndpoint
    - POST /NetworkDriver.Join
    - POST /NetworkDriver.Leave
    """
    @ddt.data(('/Plugin.Activate', constants.SCHEMA['PLUGIN_ACTIVATE']),
        ('/NetworkDriver.EndpointOperInfo',
         constants.SCHEMA['ENDPOINT_OPER_INFO']),
        ('/NetworkDriver.Leave', constants.SCHEMA['SUCCESS']))
    @ddt.unpack
    def test_remote_driver_endpoint(self, endpoint, expected):
        response = self.app.post(endpoint)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(expected, decoded_json)

    def test_network_driver_create_network(self):
        docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        self.mox.StubOutWithMock(app.neutron, "create_network")
        fake_request = {
            "network": {
                "name": docker_network_id,
                "admin_state_up": True
            }
        }
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createNetwork  # noqa
        fake_response = {
            "network": {
                "status": "ACTIVE",
                "subnets": [],
                "name": docker_network_id,
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
            }
        }
        app.neutron.create_network(fake_request).AndReturn(fake_response)

        self.mox.ReplayAll()

        data = {'NetworkID': docker_network_id, 'Options': {}}
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_delete_network(self):
        docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_neutron_network_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_network_id, docker_network_id)

        self.mox.StubOutWithMock(app.neutron, 'delete_network')
        app.neutron.delete_network(fake_neutron_network_id).AndReturn(None)
        self.mox.ReplayAll()

        data = {'NetworkID': docker_network_id}
        response = self.app.post('/NetworkDriver.DeleteNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_create_endpoint(self):
        docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()

        fake_neutron_network_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_network_id, docker_network_id)

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_existing_subnets_response = {
            "subnets": []
        }
        fake_cidr_v4 = '192.168.1.0/24'
        app.neutron.list_subnets(
            network_id=fake_neutron_network_id,
            cidr=fake_cidr_v4).AndReturn(fake_existing_subnets_response)

        fake_cidr_v6 = 'fe80::/64'
        app.neutron.list_subnets(
            network_id=fake_neutron_network_id,
            cidr=fake_cidr_v6).AndReturn(fake_existing_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'create_subnet')
        fake_subnet_request = {
            "subnets": [{
                'name': '-'.join([docker_endpoint_id,
                                  '192.168.1.0']),
                'network_id': fake_neutron_network_id,
                'allocation_pools': None,
                'ip_version': 4,
                "cidr": '192.168.1.0/24'
            }, {
                'name': '-'.join([docker_endpoint_id,
                                  'fe80::']),
                'network_id': fake_neutron_network_id,
                'allocation_pools': None,
                'ip_version': 6,
                "cidr": 'fe80::/64'
            }]
        }
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createSubnet  # noqa
        subnet_v4_id = "9436e561-47bf-436a-b1f1-fe23a926e031"
        subnet_v6_id = "64dd4a98-3d7a-4bfd-acf4-91137a8d2f51"
        fake_v4_subnet = self._get_fake_v4_subnet(
            docker_network_id, docker_endpoint_id, subnet_v4_id)
        fake_v6_subnet = self._get_fake_v6_subnet(
            docker_network_id, docker_endpoint_id, subnet_v6_id)
        fake_subnet_response = {
            "subnets": [
                fake_v4_subnet['subnet'],
                fake_v6_subnet['subnet']
            ]
        }
        app.neutron.create_subnet(
            fake_subnet_request).AndReturn(fake_subnet_response)

        fake_ipv4cidr = '192.168.1.2/24'
        fake_ipv6cidr = 'fe80::f816:3eff:fe20:57c4/64'
        subnet_v4_address = fake_ipv4cidr.split('/')[0]
        subnet_v6_address = fake_ipv6cidr.split('/')[0]
        self.mox.StubOutWithMock(app.neutron, 'create_port')
        fake_port_request = {
            'port': {
                'name': '-'.join([docker_endpoint_id, '0', 'port']),
                'admin_state_up': True,
                'mac_address': "fa:16:3e:20:57:c3",
                'network_id': fake_neutron_network_id,
                'fixed_ips': [{
                    'subnet_id': subnet_v4_id,
                    'ip_address': subnet_v4_address
                }, {
                    'subnet_id': subnet_v6_id,
                    'ip_address': subnet_v6_address
                }]
            }
        }
        fake_port_id = str(uuid.uuid4())
        fake_port = self._get_fake_port(
            docker_endpoint_id, fake_neutron_network_id,
            fake_port_id,
            subnet_v4_id, subnet_v6_id)
        app.neutron.create_port(fake_port_request).AndReturn(fake_port)
        self.mox.ReplayAll()

        data = {
            'NetworkID': docker_network_id,
            'EndpointID': docker_endpoint_id,
            'Options': {},
            'Interfaces': [{
                'ID': 0,
                'Address': fake_ipv4cidr,
                'AddressIPv6': fake_ipv6cidr,
                'MacAddress': "fa:16:3e:20:57:c3"
            }]
        }
        response = self.app.post('/NetworkDriver.CreateEndpoint',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        expected = {'Interfaces': data['Interfaces']}
        self.assertEqual(expected, decoded_json)

    def test_network_driver_delete_endpoint(self):
        docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()

        fake_neutron_network_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_network_id, docker_network_id)

        fake_subnet_v4_id = "9436e561-47bf-436a-b1f1-fe23a926e031"
        fake_subnet_v6_id = "64dd4a98-3d7a-4bfd-acf4-91137a8d2f51"
        self.mox.StubOutWithMock(app.neutron, 'delete_subnet')
        app.neutron.delete_subnet(fake_subnet_v4_id).AndReturn(None)
        app.neutron.delete_subnet(fake_subnet_v6_id).AndReturn(None)

        fake_neutron_port_id = '65c0ee9f-d634-4522-8954-51021b570b0d'
        fake_ports = self._get_fake_ports(
            docker_endpoint_id, fake_neutron_network_id, fake_neutron_port_id,
            fake_subnet_v4_id, fake_subnet_v6_id)
        self.mox.StubOutWithMock(app.neutron, 'list_ports')
        app.neutron.list_ports(
            network_id=fake_neutron_network_id).AndReturn(fake_ports)
        self.mox.StubOutWithMock(app.neutron, 'delete_port')
        app.neutron.delete_port(fake_neutron_port_id).AndReturn(None)
        self.mox.ReplayAll()

        data = {
            'NetworkID': docker_network_id,
            'EndpointID': docker_endpoint_id,
        }
        response = self.app.post('/NetworkDriver.DeleteEndpoint',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_join(self):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_container_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()

        data = {
            'NetworkID': fake_docker_network_id,
            'EndpointID': fake_docker_endpoint_id,
            'SandboxKey': utils.get_sandbox_key(fake_container_id),
            'Options': {},
        }
        response = self.app.post('/NetworkDriver.Join',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        app.logger.info(decoded_json)
        self.assertEqual(constants.SCHEMA['JOIN'], decoded_json)
