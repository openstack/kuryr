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

import uuid

import ddt
from oslo_serialization import jsonutils

from kuryr import app
from kuryr.common import config
from kuryr.common import constants
from kuryr.tests.unit import base
from kuryr import utils


@ddt.ddt
class TestKuryr(base.TestKuryrBase):
    """Basic unitests for libnetwork remote driver URI endpoints.

    This test class covers the following HTTP methods and URIs as described in
    the remote driver specification as below:

      https://github.com/docker/libnetwork/blob/3c8e06bc0580a2a1b2440fe0792fbfcd43a9feca/docs/remote.md  # noqa

    - POST /Plugin.Activate
    - POST /NetworkDriver.GetCapabilities
    - POST /NetworkDriver.CreateNetwork
    - POST /NetworkDriver.DeleteNetwork
    - POST /NetworkDriver.CreateEndpoint
    - POST /NetworkDriver.EndpointOperInfo
    - POST /NetworkDriver.DeleteEndpoint
    - POST /NetworkDriver.Join
    - POST /NetworkDriver.Leave
    - POST /NetworkDriver.DiscoverNew
    - POST /NetworkDriver.DiscoverDelete
    """
    @ddt.data(('/Plugin.Activate', constants.SCHEMA['PLUGIN_ACTIVATE']),
        ('/NetworkDriver.GetCapabilities',
         {'Scope': config.CONF.capability_scope}),
        ('/NetworkDriver.DiscoverNew', constants.SCHEMA['SUCCESS']),
        ('/NetworkDriver.DiscoverDelete', constants.SCHEMA['SUCCESS']),
        ('/NetworkDriver.EndpointOperInfo',
         constants.SCHEMA['ENDPOINT_OPER_INFO']))
    @ddt.unpack
    def test_remote_driver_endpoint(self, endpoint, expected):
        response = self.app.post(endpoint)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(expected, decoded_json)

    def test_network_driver_create_network(self):
        docker_network_id = utils.get_hash()
        self.mox.StubOutWithMock(app.neutron, "create_network")
        fake_request = {
            "network": {
                "name": utils.make_net_name(docker_network_id),
                "admin_state_up": True
            }
        }
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createNetwork  # noqa
        fake_neutron_net_id = "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
        fake_response = {
            "network": {
                "status": "ACTIVE",
                "subnets": [],
                "name": utils.make_net_name(docker_network_id),
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": fake_neutron_net_id
            }
        }
        app.neutron.create_network(fake_request).AndReturn(fake_response)

        self.mox.StubOutWithMock(app.neutron, "add_tag")
        tags = utils.create_net_tags(docker_network_id)
        for tag in tags:
            app.neutron.add_tag('networks', fake_neutron_net_id, tag)

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_existing_subnets_response = {
            "subnets": []
        }
        fake_cidr_v4 = '192.168.42.0/24'
        app.neutron.list_subnets(
            network_id=fake_neutron_net_id,
            cidr=fake_cidr_v4).AndReturn(fake_existing_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'create_subnet')
        fake_subnet_request = {
            "subnets": [{
                'name': fake_cidr_v4,
                'network_id': fake_neutron_net_id,
                'ip_version': 4,
                'cidr': fake_cidr_v4,
                'enable_dhcp': app.enable_dhcp,
                'gateway_ip': '192.168.42.1',
            }]
        }
        subnet_v4_id = str(uuid.uuid4())
        fake_v4_subnet = self._get_fake_v4_subnet(
            fake_neutron_net_id, subnet_v4_id,
            name=fake_cidr_v4, cidr=fake_cidr_v4)
        fake_subnet_response = {
            'subnets': [
                fake_v4_subnet['subnet']
            ]
        }
        app.neutron.create_subnet(
            fake_subnet_request).AndReturn(fake_subnet_response)

        self.mox.ReplayAll()

        network_request = {
            'NetworkID': docker_network_id,
            'IPv4Data': [{
                'AddressSpace': 'foo',
                'Pool': '192.168.42.0/24',
                'Gateway': '192.168.42.1/24',
            }],
            'IPv6Data': [{
                'AddressSpace': 'bar',
                'Pool': 'fe80::/64',
                'Gateway': 'fe80::f816:3eff:fe20:57c3/64',
            }],
            'Options': {}
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_create_network_with_net_name_option(self):
        docker_network_id = utils.get_hash()
        fake_neutron_net_id = "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
        self.mox.StubOutWithMock(app.neutron, "list_networks")
        fake_neutron_net_name = 'my_network_name'
        fake_existing_networks_response = {
            "networks": [{
                "status": "ACTIVE",
                "subnets": [],
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": fake_neutron_net_id,
                "name": "my_network_name"
            }]
        }
        app.neutron.list_networks(
            name=fake_neutron_net_name).AndReturn(
                fake_existing_networks_response)

        self.mox.StubOutWithMock(app.neutron, "add_tag")
        tags = utils.create_net_tags(docker_network_id)
        for tag in tags:
            app.neutron.add_tag('networks', fake_neutron_net_id, tag)

        app.neutron.add_tag(
            'networks', fake_neutron_net_id, 'kuryr.net.existing')
        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_existing_subnets_response = {
            "subnets": []
        }
        fake_cidr_v4 = '192.168.42.0/24'
        app.neutron.list_subnets(
            network_id=fake_neutron_net_id,
            cidr=fake_cidr_v4).AndReturn(fake_existing_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'create_subnet')
        fake_subnet_request = {
            "subnets": [{
                'name': fake_cidr_v4,
                'network_id': fake_neutron_net_id,
                'ip_version': 4,
                'cidr': fake_cidr_v4,
                'enable_dhcp': app.enable_dhcp,
                'gateway_ip': '192.168.42.1',
            }]
        }
        subnet_v4_id = str(uuid.uuid4())
        fake_v4_subnet = self._get_fake_v4_subnet(
            fake_neutron_net_id, subnet_v4_id,
            name=fake_cidr_v4, cidr=fake_cidr_v4)
        fake_subnet_response = {
            'subnets': [
                fake_v4_subnet['subnet']
            ]
        }
        app.neutron.create_subnet(
            fake_subnet_request).AndReturn(fake_subnet_response)

        self.mox.ReplayAll()

        network_request = {
            'NetworkID': docker_network_id,
            'IPv4Data': [{
                'AddressSpace': 'foo',
                'Pool': '192.168.42.0/24',
                'Gateway': '192.168.42.1/24',
            }],
            'IPv6Data': [{
                'AddressSpace': 'bar',
                'Pool': 'fe80::/64',
                'Gateway': 'fe80::f816:3eff:fe20:57c3/64',
            }],
            'Options': {
                'com.docker.network.enable_ipv6': False,
                'com.docker.network.generic': {
                    'neutron.net.name': 'my_network_name'
                }
            }
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_create_network_with_netid_option(self):
        docker_network_id = utils.get_hash()
        fake_neutron_net_id = "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
        self.mox.StubOutWithMock(app.neutron, "list_networks")
        fake_existing_networks_response = {
            "networks": [{
                "status": "ACTIVE",
                "subnets": [],
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": fake_neutron_net_id,
            }]
        }
        app.neutron.list_networks(
            id=fake_neutron_net_id).AndReturn(
                fake_existing_networks_response)

        self.mox.StubOutWithMock(app.neutron, "add_tag")
        tags = utils.create_net_tags(docker_network_id)
        for tag in tags:
            app.neutron.add_tag('networks', fake_neutron_net_id, tag)

        app.neutron.add_tag(
            'networks', fake_neutron_net_id, 'kuryr.net.existing')
        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_existing_subnets_response = {
            "subnets": []
        }
        fake_cidr_v4 = '192.168.42.0/24'
        app.neutron.list_subnets(
            network_id=fake_neutron_net_id,
            cidr=fake_cidr_v4).AndReturn(fake_existing_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'create_subnet')
        fake_subnet_request = {
            "subnets": [{
                'name': fake_cidr_v4,
                'network_id': fake_neutron_net_id,
                'ip_version': 4,
                'cidr': fake_cidr_v4,
                'enable_dhcp': app.enable_dhcp,
                'gateway_ip': '192.168.42.1',
            }]
        }
        subnet_v4_id = str(uuid.uuid4())
        fake_v4_subnet = self._get_fake_v4_subnet(
            fake_neutron_net_id, subnet_v4_id,
            name=fake_cidr_v4, cidr=fake_cidr_v4)
        fake_subnet_response = {
            'subnets': [
                fake_v4_subnet['subnet']
            ]
        }
        app.neutron.create_subnet(
            fake_subnet_request).AndReturn(fake_subnet_response)

        self.mox.ReplayAll()

        network_request = {
            'NetworkID': docker_network_id,
            'IPv4Data': [{
                'AddressSpace': 'foo',
                'Pool': '192.168.42.0/24',
                'Gateway': '192.168.42.1/24',
            }],
            'IPv6Data': [{
                'AddressSpace': 'bar',
                'Pool': 'fe80::/64',
                'Gateway': 'fe80::f816:3eff:fe20:57c3/64',
            }],
            'Options': {
                'com.docker.network.enable_ipv6': False,
                'com.docker.network.generic': {
                    'neutron.net.uuid': '4e8e5957-649f-477b-9e5b-f1f75b21c03c'
                }
            }
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_create_network_with_pool_name_option(self):

        self.mox.StubOutWithMock(app.neutron, 'list_subnetpools')
        fake_kuryr_subnetpool_id = str(uuid.uuid4())
        fake_name = "fake_pool_name"
        kuryr_subnetpools = self._get_fake_v4_subnetpools(
            fake_kuryr_subnetpool_id, name=fake_name)
        app.neutron.list_subnetpools(name=fake_name).AndReturn(
            {'subnetpools': kuryr_subnetpools['subnetpools']})
        docker_network_id = utils.get_hash()
        self.mox.StubOutWithMock(app.neutron, "create_network")
        fake_request = {
            "network": {
                "name": utils.make_net_name(docker_network_id),
                "admin_state_up": True
            }
        }
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createNetwork  # noqa
        fake_neutron_net_id = "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
        fake_response = {
            "network": {
                "status": "ACTIVE",
                "subnets": [],
                "name": utils.make_net_name(docker_network_id),
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": fake_neutron_net_id
            }
        }
        app.neutron.create_network(fake_request).AndReturn(fake_response)

        self.mox.StubOutWithMock(app.neutron, "add_tag")
        tags = utils.create_net_tags(docker_network_id)
        for tag in tags:
            app.neutron.add_tag('networks', fake_neutron_net_id, tag)

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_existing_subnets_response = {
            "subnets": []
        }
        fake_cidr_v4 = '192.168.42.0/24'
        app.neutron.list_subnets(
            network_id=fake_neutron_net_id,
            cidr=fake_cidr_v4).AndReturn(fake_existing_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'create_subnet')
        fake_subnet_request = {
            "subnets": [{
                'name': fake_cidr_v4,
                'network_id': fake_neutron_net_id,
                'ip_version': 4,
                'cidr': fake_cidr_v4,
                'enable_dhcp': app.enable_dhcp,
                'gateway_ip': '192.168.42.1',
                'subnetpool_id': fake_kuryr_subnetpool_id,
            }]
        }
        subnet_v4_id = str(uuid.uuid4())
        fake_v4_subnet = self._get_fake_v4_subnet(
            fake_neutron_net_id, subnet_v4_id,
            name=fake_cidr_v4, cidr=fake_cidr_v4)
        fake_subnet_response = {
            'subnets': [
                fake_v4_subnet['subnet']
            ]
        }
        app.neutron.create_subnet(
            fake_subnet_request).AndReturn(fake_subnet_response)

        self.mox.ReplayAll()

        network_request = {
            'NetworkID': docker_network_id,
            'IPv4Data': [{
                'AddressSpace': 'foo',
                'Pool': '192.168.42.0/24',
                'Gateway': '192.168.42.1/24',
            }],
            'IPv6Data': [{
                'AddressSpace': 'bar',
                'Pool': 'fe80::/64',
                'Gateway': 'fe80::f816:3eff:fe20:57c3/64',
            }],
            'Options': {
                'com.docker.network.enable_ipv6': False,
                'com.docker.network.generic': {
                    'neutron.pool.name': 'fake_pool_name'
                }
            }
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_create_network_wo_gw(self):
        docker_network_id = utils.get_hash()
        self.mox.StubOutWithMock(app.neutron, "create_network")
        fake_request = {
            "network": {
                "name": utils.make_net_name(docker_network_id),
                "admin_state_up": True
            }
        }
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createNetwork  # noqa
        fake_neutron_net_id = "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
        fake_response = {
            "network": {
                "status": "ACTIVE",
                "subnets": [],
                "name": utils.make_net_name(docker_network_id),
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": fake_neutron_net_id
            }
        }
        app.neutron.create_network(fake_request).AndReturn(fake_response)

        self.mox.StubOutWithMock(app.neutron, "add_tag")
        tags = utils.create_net_tags(docker_network_id)
        for tag in tags:
            app.neutron.add_tag('networks', fake_neutron_net_id, tag)

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_existing_subnets_response = {
            "subnets": []
        }
        fake_cidr_v4 = '192.168.42.0/24'
        app.neutron.list_subnets(
            network_id=fake_neutron_net_id,
            cidr=fake_cidr_v4).AndReturn(fake_existing_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'create_subnet')
        fake_subnet_request = {
            "subnets": [{
                'name': fake_cidr_v4,
                'network_id': fake_neutron_net_id,
                'ip_version': 4,
                'cidr': fake_cidr_v4,
                'enable_dhcp': app.enable_dhcp,
            }]
        }
        subnet_v4_id = str(uuid.uuid4())
        fake_v4_subnet = self._get_fake_v4_subnet(
            fake_neutron_net_id, subnet_v4_id,
            name=fake_cidr_v4, cidr=fake_cidr_v4)
        fake_subnet_response = {
            'subnets': [
                fake_v4_subnet['subnet']
            ]
        }
        app.neutron.create_subnet(
            fake_subnet_request).AndReturn(fake_subnet_response)

        self.mox.ReplayAll()

        network_request = {
            'NetworkID': docker_network_id,
            'IPv4Data': [{
                'AddressSpace': 'foo',
                'Pool': '192.168.42.0/24',
            }],
            'IPv6Data': [{
                'AddressSpace': 'bar',
                'Pool': 'fe80::/64',
                'Gateway': 'fe80::f816:3eff:fe20:57c3/64',
            }],
            'Options': {}
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_create_network_with_network_id_not_exist(self):
        docker_network_id = utils.get_hash()

        self.mox.StubOutWithMock(app.neutron, "list_networks")
        fake_neutron_net_id = str(uuid.uuid4())
        fake_existing_networks_response = {
            "networks": []
        }
        app.neutron.list_networks(
            id=fake_neutron_net_id).AndReturn(
                fake_existing_networks_response)
        self.mox.ReplayAll()
        network_request = {
            'NetworkID': docker_network_id,
            'IPv4Data': [{
                'AddressSpace': 'foo',
                'Pool': '192.168.42.0/24',
            }],
            'IPv6Data': [{
                'AddressSpace': 'bar',
                'Pool': 'fe80::/64',
                'Gateway': 'fe80::f816:3eff:fe20:57c3/64',
            }],
            'Options': {
                 constants.NETWORK_GENERIC_OPTIONS: {
                     constants.NEUTRON_UUID_OPTION: fake_neutron_net_id
                 }
            }
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))
        self.assertEqual(500, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        err_message = ("Specified network id/name({0}) does not "
                      "exist.").format(fake_neutron_net_id)
        self.assertEqual({'Err': err_message}, decoded_json)

    def test_network_driver_create_network_with_network_name_not_exist(self):
        docker_network_id = utils.get_hash()

        self.mox.StubOutWithMock(app.neutron, "list_networks")
        fake_neutron_network_name = "fake_network"
        fake_existing_networks_response = {
            "networks": []
        }
        app.neutron.list_networks(
            name=fake_neutron_network_name).AndReturn(
                fake_existing_networks_response)
        self.mox.ReplayAll()
        network_request = {
            'NetworkID': docker_network_id,
            'IPv4Data': [{
                'AddressSpace': 'foo',
                'Pool': '192.168.42.0/24',
            }],
            'IPv6Data': [{
                'AddressSpace': 'bar',
                'Pool': 'fe80::/64',
                'Gateway': 'fe80::f816:3eff:fe20:57c3/64',
            }],
            'Options': {
                 constants.NETWORK_GENERIC_OPTIONS: {
                     constants.NEUTRON_NAME_OPTION: fake_neutron_network_name
                 }
            }
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))
        self.assertEqual(500, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        err_message = ("Specified network id/name({0}) does not "
                      "exist.").format(fake_neutron_network_name)
        self.assertEqual({'Err': err_message}, decoded_json)

    def test_network_driver_delete_network(self):
        docker_network_id = utils.get_hash()
        fake_neutron_net_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_net_id, docker_network_id,
                               check_existing=True)
        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_neutron_subnets_response = {"subnets": []}
        app.neutron.list_subnets(network_id=fake_neutron_net_id).AndReturn(
            fake_neutron_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'delete_network')
        app.neutron.delete_network(fake_neutron_net_id).AndReturn(None)
        self.mox.ReplayAll()

        data = {'NetworkID': docker_network_id}
        response = self.app.post('/NetworkDriver.DeleteNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_delete_network_with_subnets(self):
        docker_network_id = utils.get_hash()
        docker_endpoint_id = utils.get_hash()

        fake_neutron_net_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_net_id, docker_network_id,
                               check_existing=True)
        # The following fake response is retrieved from the Neutron doc:
        # http://developer.openstack.org/api-ref-networking-v2.html#createSubnet  # noqa
        subnet_v4_id = "9436e561-47bf-436a-b1f1-fe23a926e031"
        subnet_v6_id = "64dd4a98-3d7a-4bfd-acf4-91137a8d2f51"
        fake_v4_subnet = self._get_fake_v4_subnet(
            docker_network_id, docker_endpoint_id, subnet_v4_id)
        fake_v6_subnet = self._get_fake_v6_subnet(
            docker_network_id, docker_endpoint_id, subnet_v6_id)
        fake_subnets_response = {
            "subnets": [
                fake_v4_subnet['subnet'],
                fake_v6_subnet['subnet']
            ]
        }

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        app.neutron.list_subnets(network_id=fake_neutron_net_id).AndReturn(
            fake_subnets_response)

        self.mox.StubOutWithMock(app.neutron, 'list_subnetpools')
        fake_subnetpools_response = {"subnetpools": []}
        app.neutron.list_subnetpools(name='kuryr').AndReturn(
            fake_subnetpools_response)
        app.neutron.list_subnetpools(name='kuryr6').AndReturn(
            fake_subnetpools_response)

        self.mox.StubOutWithMock(app.neutron, 'delete_subnet')
        app.neutron.delete_subnet(subnet_v4_id).AndReturn(None)
        app.neutron.delete_subnet(subnet_v6_id).AndReturn(None)

        self.mox.StubOutWithMock(app.neutron, 'delete_network')
        app.neutron.delete_network(fake_neutron_net_id).AndReturn(None)
        self.mox.ReplayAll()

        data = {'NetworkID': docker_network_id}
        response = self.app.post('/NetworkDriver.DeleteNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)

    def test_network_driver_create_endpoint(self):
        docker_network_id = utils.get_hash()
        docker_endpoint_id = utils.get_hash()

        fake_neutron_net_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_net_id, docker_network_id)

        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createSubnet  # noqa
        subnet_v4_id = "9436e561-47bf-436a-b1f1-fe23a926e031"
        subnet_v6_id = "64dd4a98-3d7a-4bfd-acf4-91137a8d2f51"
        fake_v4_subnet = self._get_fake_v4_subnet(
            docker_network_id, docker_endpoint_id, subnet_v4_id)
        fake_v6_subnet = self._get_fake_v6_subnet(
            docker_network_id, docker_endpoint_id, subnet_v6_id)

        fake_subnetv4_response = {
            "subnets": [
                fake_v4_subnet['subnet']
            ]
        }
        fake_subnetv6_response = {
            "subnets": [
                fake_v6_subnet['subnet']
            ]
        }

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        app.neutron.list_subnets(network_id=fake_neutron_net_id,
            cidr='192.168.1.0/24').AndReturn(fake_subnetv4_response)
        app.neutron.list_subnets(
            network_id=fake_neutron_net_id,
            cidr='fe80::/64').AndReturn(fake_subnetv6_response)

        fake_ipv4cidr = '192.168.1.2/24'
        fake_ipv6cidr = 'fe80::f816:3eff:fe20:57c4/64'
        fake_port_id = str(uuid.uuid4())
        fake_port = self._get_fake_port(
            docker_endpoint_id, fake_neutron_net_id,
            fake_port_id, constants.PORT_STATUS_ACTIVE,
            subnet_v4_id, subnet_v6_id)
        fake_fixed_ips = ['subnet_id=%s' % subnet_v4_id,
                          'ip_address=192.168.1.2',
                          'subnet_id=%s' % subnet_v6_id,
                          'ip_address=fe80::f816:3eff:fe20:57c4']
        fake_port_response = {
            "ports": [
                fake_port['port']
            ]
        }
        self.mox.StubOutWithMock(app.neutron, 'list_ports')
        app.neutron.list_ports(fixed_ips=fake_fixed_ips).AndReturn(
            fake_port_response)
        fake_updated_port = fake_port['port']
        fake_updated_port['name'] = '-'.join([docker_endpoint_id, 'port'])
        self.mox.StubOutWithMock(app.neutron, 'update_port')
        app.neutron.update_port(fake_updated_port['id'], {'port': {
            'name': fake_updated_port['name'],
            'device_owner': constants.DEVICE_OWNER,
            'device_id': docker_endpoint_id}}).AndReturn(fake_port)
        self.mox.ReplayAll()

        data = {
            'NetworkID': docker_network_id,
            'EndpointID': docker_endpoint_id,
            'Options': {},
            'Interface': {
                'Address': fake_ipv4cidr,
                'AddressIPv6': fake_ipv6cidr,
                'MacAddress': "fa:16:3e:20:57:c3"
            }
        }
        response = self.app.post('/NetworkDriver.CreateEndpoint',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        expected = {'Interface': {}}
        self.assertEqual(expected, decoded_json)

    def test_network_driver_delete_endpoint(self):
        docker_network_id = utils.get_hash()
        docker_endpoint_id = utils.get_hash()
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

    @ddt.data(
        (False), (True))
    def test_network_driver_join(self, vif_plug_is_fatal):
        if vif_plug_is_fatal:
            self.mox.StubOutWithMock(app, "vif_plug_is_fatal")
            app.vif_plug_is_fatal = True

        fake_docker_net_id = utils.get_hash()
        fake_docker_endpoint_id = utils.get_hash()
        fake_container_id = utils.get_hash()

        fake_neutron_net_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_net_id, fake_docker_net_id)
        fake_neutron_port_id = str(uuid.uuid4())
        self.mox.StubOutWithMock(app.neutron, 'list_ports')
        neutron_port_name = utils.get_neutron_port_name(
            fake_docker_endpoint_id)
        fake_neutron_v4_subnet_id = str(uuid.uuid4())
        fake_neutron_v6_subnet_id = str(uuid.uuid4())
        fake_neutron_ports_response = self._get_fake_ports(
            fake_docker_endpoint_id, fake_neutron_net_id,
            fake_neutron_port_id, constants.PORT_STATUS_DOWN,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        app.neutron.list_ports(name=neutron_port_name).AndReturn(
            fake_neutron_ports_response)

        self.mox.StubOutWithMock(app.neutron, 'list_subnets')
        fake_neutron_subnets_response = self._get_fake_subnets(
            fake_docker_endpoint_id, fake_neutron_net_id,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        app.neutron.list_subnets(network_id=fake_neutron_net_id).AndReturn(
            fake_neutron_subnets_response)
        fake_neutron_port = fake_neutron_ports_response['ports'][0]
        fake_neutron_subnets = fake_neutron_subnets_response['subnets']
        _, fake_peer_name, _ = self._mock_out_binding(
            fake_docker_endpoint_id, fake_neutron_port, fake_neutron_subnets)

        if vif_plug_is_fatal:
            self.mox.StubOutWithMock(app.neutron, 'show_port')
            fake_neutron_ports_response_2 = self._get_fake_port(
                fake_docker_endpoint_id, fake_neutron_net_id,
                fake_neutron_port_id, constants.PORT_STATUS_ACTIVE,
                fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
            app.neutron.show_port(fake_neutron_port_id).AndReturn(
                fake_neutron_ports_response_2)

        self.mox.ReplayAll()

        fake_subnets_dict_by_id = {subnet['id']: subnet
                                   for subnet in fake_neutron_subnets}

        join_request = {
            'NetworkID': fake_docker_net_id,
            'EndpointID': fake_docker_endpoint_id,
            'SandboxKey': utils.get_sandbox_key(fake_container_id),
            'Options': {},
        }
        response = self.app.post('/NetworkDriver.Join',
                                 content_type='application/json',
                                 data=jsonutils.dumps(join_request))

        self.assertEqual(200, response.status_code)

        decoded_json = jsonutils.loads(response.data)
        fake_neutron_v4_subnet = fake_subnets_dict_by_id[
            fake_neutron_v4_subnet_id]
        fake_neutron_v6_subnet = fake_subnets_dict_by_id[
            fake_neutron_v6_subnet_id]
        expected_response = {
            'Gateway': fake_neutron_v4_subnet['gateway_ip'],
            'GatewayIPv6': fake_neutron_v6_subnet['gateway_ip'],
            'InterfaceName': {
                'DstPrefix': config.CONF.binding.veth_dst_prefix,
                'SrcName': fake_peer_name,
            },
            'StaticRoutes': []
        }
        self.assertEqual(expected_response, decoded_json)

    def test_network_driver_leave(self):
        fake_docker_net_id = utils.get_hash()
        fake_docker_endpoint_id = utils.get_hash()

        fake_neutron_net_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_net_id, fake_docker_net_id)
        fake_neutron_port_id = str(uuid.uuid4())
        self.mox.StubOutWithMock(app.neutron, 'list_ports')
        neutron_port_name = utils.get_neutron_port_name(
            fake_docker_endpoint_id)
        fake_neutron_v4_subnet_id = str(uuid.uuid4())
        fake_neutron_v6_subnet_id = str(uuid.uuid4())
        fake_neutron_ports_response = self._get_fake_ports(
            fake_docker_endpoint_id, fake_neutron_net_id,
            fake_neutron_port_id, constants.PORT_STATUS_ACTIVE,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        app.neutron.list_ports(name=neutron_port_name).AndReturn(
            fake_neutron_ports_response)

        fake_neutron_port = fake_neutron_ports_response['ports'][0]
        self._mock_out_unbinding(fake_docker_endpoint_id, fake_neutron_port)

        leave_request = {
            'NetworkID': fake_docker_net_id,
            'EndpointID': fake_docker_endpoint_id,
        }
        response = self.app.post('/NetworkDriver.Leave',
                                 content_type='application/json',
                                 data=jsonutils.dumps(leave_request))

        self.mox.ReplayAll()
        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(constants.SCHEMA['SUCCESS'], decoded_json)
