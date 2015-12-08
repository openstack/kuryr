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
from neutronclient.common import exceptions
from oslo_serialization import jsonutils

from kuryr import app
from kuryr.common import constants
from kuryr.tests.unit import base
from kuryr import utils


class TestKuryrEndpointFailures(base.TestKuryrFailures):
    """Base class that has the methods commonly shared among endpoint tests.

    This class mainly has the methods for mocking API calls against Neutron.
    """
    def _create_subnet_with_exception(self, neutron_network_id,
                                      docker_endpoint_id, ex):
        fake_neutron_subnet_v4_id = str(uuid.uuid4())
        fake_neutron_subnet_v6_id = str(uuid.uuid4())

        self.mox.StubOutWithMock(app.neutron, 'create_subnet')
        fake_subnet_request = {
            'subnets': [{
                'name': '-'.join([docker_endpoint_id, '192.168.1.0']),
                'network_id': neutron_network_id,
                'ip_version': 4,
                "cidr": '192.168.1.0/24',
                'enable_dhcp': 'False'
            }, {
                'name': '-'.join([docker_endpoint_id, 'fe80::']),
                'network_id': neutron_network_id,
                'ip_version': 6,
                "cidr": 'fe80::/64',
                'enable_dhcp': 'False'
            }]
        }
        fake_subnets = self._get_fake_subnets(
            docker_endpoint_id, neutron_network_id,
            fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id)

        if ex:
            app.neutron.create_subnet(fake_subnet_request).AndRaise(ex)
        else:
            app.neutron.create_subnet(
                fake_subnet_request).AndReturn(fake_subnets)
        self.mox.ReplayAll()

        return (fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id)

    def _delete_subnet_with_exception(self, neutron_subnet_id, ex):
        self.mox.StubOutWithMock(app.neutron, 'delete_subnet')
        if ex:
            app.neutron.delete_subnet(neutron_subnet_id).AndRaise(ex)
        else:
            app.neutron.delete_subnet(neutron_subnet_id).AndReturn(None)
        self.mox.ReplayAll()

    def _delete_subnets_with_exception(self, neutron_subnet_ids, ex):
        self.mox.StubOutWithMock(app.neutron, 'delete_subnet')
        for neutron_subnet_id in neutron_subnet_ids:
            if ex:
                app.neutron.delete_subnet(neutron_subnet_id).AndRaise(ex)
            else:
                app.neutron.delete_subnet(neutron_subnet_id).AndReturn(None)
        self.mox.ReplayAll()

    def _create_port_with_exception(self, neutron_network_id,
                                    docker_endpoint_id, neutron_subnetv4_id,
                                    neutron_subnetv6_id, ex):
        self.mox.StubOutWithMock(app.neutron, 'create_port')
        fake_port_request = {
            'port': {
                'name': utils.get_neutron_port_name(docker_endpoint_id),
                'admin_state_up': True,
                "binding:host_id": utils.get_hostname(),
                'device_owner': constants.DEVICE_OWNER,
                'device_id': docker_endpoint_id,
                'fixed_ips': [{
                    'subnet_id': neutron_subnetv4_id,
                    'ip_address': '192.168.1.2'
                }, {
                    'subnet_id': neutron_subnetv6_id,
                    'ip_address': 'fe80::f816:3eff:fe20:57c4'
                }],
                'mac_address': "fa:16:3e:20:57:c3",
                'network_id': neutron_network_id
            }
        }
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createPort  # noqa
        fake_port = {
            "port": {
                "status": "DOWN",
                "name": utils.get_neutron_port_name(docker_endpoint_id),
                "allowed_address_pairs": [],
                "admin_state_up": True,
                "binding:host_id": utils.get_hostname(),
                "network_id": neutron_network_id,
                "tenant_id": "d6700c0c9ffa4f1cb322cd4a1f3906fa",
                "device_owner": constants.DEVICE_OWNER,
                'device_id': docker_endpoint_id,
                "mac_address": "fa:16:3e:20:57:c3",
                'fixed_ips': [{
                    'subnet_id': neutron_subnetv4_id,
                    'ip_address': '192.168.1.2'
                }, {
                    'subnet_id': neutron_subnetv6_id,
                    'ip_address': 'fe80::f816:3eff:fe20:57c4'
                }],
                "id": "65c0ee9f-d634-4522-8954-51021b570b0d",
                "security_groups": [],
                "device_id": ""
            }
        }
        if ex:
            app.neutron.create_port(fake_port_request).AndRaise(ex)
        else:
            app.neutron.create_port(fake_port_request).AndReturn(fake_port)
        self.mox.ReplayAll()

    def _delete_port_with_exception(self, neutron_port_id, ex):
        self.mox.StubOutWithMock(app.neutron, "delete_port")
        if ex:
            app.neutron.delete_port(neutron_port_id).AndRaise(ex)
        else:
            app.neutron.delete_port(neutron_port_id).AndReturn(None)
        self.mox.ReplayAll()


@ddt.ddt
class TestKuryrEndpointCreateFailures(TestKuryrEndpointFailures):
    """Unit tests for the failures for creating endpoints.

    This test covers error responses listed in the spec:
      http://developer.openstack.org/api-ref-networking-v2.html#createSubnet  # noqa
      http://developer.openstack.org/api-ref-networking-v2-ext.html#createPort  # noqa
    """
    def _invoke_create_request(self, docker_network_id, docker_endpoint_id):
        data = {
            'NetworkID': docker_network_id,
            'EndpointID': docker_endpoint_id,
            'Options': {},
            'Interface': {
                'Address': '192.168.1.2/24',
                'AddressIPv6': 'fe80::f816:3eff:fe20:57c4/64',
                'MacAddress': "fa:16:3e:20:57:c3"
            }
        }
        response = self.app.post('/NetworkDriver.CreateEndpoint',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))
        return response

    @ddt.data(exceptions.Unauthorized, exceptions.Forbidden,
              exceptions.NotFound, exceptions.Conflict)
    def test_create_endpoint_subnet_failures(self, GivenException):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_neutron_network_id = str(uuid.uuid4())

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        app.neutron.list_subnets(
            network_id=fake_neutron_network_id,
            cidr='192.168.1.0/24').AndReturn({'subnets': []})
        app.neutron.list_subnets(
            network_id=fake_neutron_network_id,
            cidr='fe80::/64').AndReturn({'subnets': []})

        self._create_subnet_with_exception(
            fake_neutron_network_id, fake_docker_endpoint_id, GivenException())
        self._mock_out_network(fake_neutron_network_id, fake_docker_network_id)

        response = self._invoke_create_request(
            fake_docker_network_id, fake_docker_endpoint_id)

        self.assertEqual(GivenException.status_code, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        self.assertEqual({'Err': GivenException.message}, decoded_json)

    @ddt.data(exceptions.Unauthorized, exceptions.Forbidden,
              exceptions.NotFound, exceptions.ServiceUnavailable)
    def test_create_endpoint_port_failures(self, GivenException):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_neutron_network_id = str(uuid.uuid4())

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        app.neutron.list_subnets(
            network_id=fake_neutron_network_id,
            cidr='192.168.1.0/24').AndReturn({'subnets': []})
        app.neutron.list_subnets(
            network_id=fake_neutron_network_id,
            cidr='fe80::/64').AndReturn({'subnets': []})

        (fake_neutron_subnet_v4_id,
         fake_neutron_subnet_v6_id) = self._create_subnet_with_exception(
            fake_neutron_network_id, fake_docker_endpoint_id, None)
        self._create_port_with_exception(fake_neutron_network_id,
                                         fake_docker_endpoint_id,
                                         fake_neutron_subnet_v4_id,
                                         fake_neutron_subnet_v6_id,
                                         GivenException())
        self._mock_out_network(fake_neutron_network_id, fake_docker_network_id)

        # The port creation is failed and Kuryr rolles the created subnet back.
        self._delete_subnets_with_exception(
            [fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id], None)

        response = self._invoke_create_request(
            fake_docker_network_id, fake_docker_endpoint_id)

        self.assertEqual(GivenException.status_code, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        self.assertEqual({'Err': GivenException.message}, decoded_json)

    def test_create_endpoint_bad_request(self):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        invalid_docker_endpoint_id = 'id-should-be-hexdigits'

        response = self._invoke_create_request(
            fake_docker_network_id, invalid_docker_endpoint_id)

        self.assertEqual(400, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        # TODO(tfukushima): Add the better error message validation.
        self.assertIn(invalid_docker_endpoint_id, decoded_json['Err'])
        self.assertIn('EndpointID', decoded_json['Err'])


@ddt.ddt
class TestKuryrEndpointDeleteFailures(TestKuryrEndpointFailures):
    """Unit tests for the failures for deleting endpoints.

    This test covers error responses listed in the spec:
      http://developer.openstack.org/api-ref-networking-v2-ext.html#deleteProviderNetwork  # noqa
    """
    def _invoke_delete_request(self, docker_network_id, docker_endpoint_id):
        data = {'NetworkID': docker_network_id,
                'EndpointID': docker_endpoint_id}
        response = self.app.post('/NetworkDriver.DeleteEndpoint',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))
        return response

    @ddt.data(exceptions.Unauthorized, exceptions.NotFound,
              exceptions.Conflict)
    def test_delete_endpoint_subnet_failures(self, GivenException):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_neutron_network_id = str(uuid.uuid4())
        fake_neutron_port_id = str(uuid.uuid4())
        fake_neutron_subnet_v4_id = str(uuid.uuid4())
        fake_neutron_subnet_v6_id = str(uuid.uuid4())

        self._mock_out_network(fake_neutron_network_id, fake_docker_network_id)

        self.mox.StubOutWithMock(app.neutron, 'list_subnetpools')
        fake_default_v4_subnetpool_id = str(uuid.uuid4())
        app.neutron.list_subnetpools(name='kuryr').AndReturn(
            self._get_fake_v4_subnetpools(
                fake_default_v4_subnetpool_id))
        fake_default_v6_subnetpool_id = str(uuid.uuid4())
        app.neutron.list_subnetpools(name='kuryr6').AndReturn(
            self._get_fake_v6_subnetpools(
                fake_default_v6_subnetpool_id))

        fake_ports = self._get_fake_ports(
            fake_docker_endpoint_id, fake_neutron_network_id,
            fake_neutron_port_id,
            fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id)
        self.mox.StubOutWithMock(app.neutron, 'list_ports')
        app.neutron.list_ports(
            network_id=fake_neutron_network_id).AndReturn(fake_ports)
        self.mox.StubOutWithMock(app.neutron, 'delete_port')
        app.neutron.delete_port(fake_neutron_port_id).AndReturn(None)

        self.mox.StubOutWithMock(app.neutron, 'show_subnet')
        fake_v4_subnet = self._get_fake_v4_subnet(
            fake_docker_network_id, fake_docker_endpoint_id,
            fake_neutron_subnet_v4_id)
        app.neutron.show_subnet(
            fake_neutron_subnet_v4_id).AndReturn(fake_v4_subnet)

        if GivenException is exceptions.Conflict:
            fake_v6_subnet = self._get_fake_v6_subnet(
                fake_docker_network_id, fake_docker_endpoint_id,
                fake_neutron_subnet_v6_id)
            app.neutron.show_subnet(
                fake_neutron_subnet_v6_id).AndReturn(fake_v6_subnet)

        self.mox.ReplayAll()

        if GivenException is exceptions.Conflict:
            self._delete_subnets_with_exception(
                [fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id],
                GivenException())
        else:
            self._delete_subnet_with_exception(
                fake_neutron_subnet_v4_id, GivenException())

        response = self._invoke_delete_request(
            fake_docker_network_id, fake_docker_endpoint_id)

        if GivenException is exceptions.Conflict:
            self.assertEqual(200, response.status_code)
            decoded_json = jsonutils.loads(response.data)
            self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)
        else:
            self.assertEqual(GivenException.status_code, response.status_code)
            decoded_json = jsonutils.loads(response.data)
            self.assertIn('Err', decoded_json)
            self.assertEqual({'Err': GivenException.message}, decoded_json)

    @ddt.data(exceptions.Unauthorized, exceptions.NotFound,
              exceptions.Conflict)
    def test_delete_endpiont_port_failures(self, GivenException):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_neutron_network_id = str(uuid.uuid4())
        fake_neutron_subnet_v4_id = str(uuid.uuid4())
        fake_neutron_subnet_v6_id = str(uuid.uuid4())
        fake_neutron_port_id = str(uuid.uuid4())

        self._mock_out_network(fake_neutron_network_id, fake_docker_network_id)
        self.mox.StubOutWithMock(app.neutron, 'list_ports')
        fake_ports = self._get_fake_ports(
            fake_docker_endpoint_id, fake_neutron_network_id,
            fake_neutron_port_id,
            fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id)
        app.neutron.list_ports(
            network_id=fake_neutron_network_id).AndReturn(fake_ports)
        self._delete_port_with_exception(fake_neutron_port_id, GivenException)

        response = self._invoke_delete_request(
            fake_docker_network_id, fake_docker_endpoint_id)

        self.assertEqual(GivenException.status_code, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        self.assertEqual({'Err': GivenException.message}, decoded_json)

    def test_delete_endpoint_bad_request(self):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        invalid_docker_endpoint_id = 'id-should-be-hexdigits'

        response = self._invoke_delete_request(
            fake_docker_network_id, invalid_docker_endpoint_id)

        self.assertEqual(400, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        # TODO(tfukushima): Add the better error message validation.
        self.assertIn(invalid_docker_endpoint_id, decoded_json['Err'])
        self.assertIn('EndpointID', decoded_json['Err'])
