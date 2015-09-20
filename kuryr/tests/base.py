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

from neutronclient.tests.unit import test_cli20

from kuryr import app


class TestCase(test_cli20.CLITestV20Base):
    """Test case base class for all unit tests."""

    def setUp(self):
        super(TestCase, self).setUp()
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.app.neutron = self.client


class TestKuryrBase(TestCase):
    """Base class for all Kuryr unittests."""

    def setUp(self):
        super(TestKuryrBase, self).setUp()
        self.app.neutron.format = 'json'
        self.addCleanup(self.mox.VerifyAll)
        self.addCleanup(self.mox.UnsetStubs)

    def _mock_out_network(self, neutron_network_id, docker_network_id):
        fake_list_response = {
            "networks": [{
                "status": "ACTIVE",
                "subnets": [],
                "name": docker_network_id,
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": neutron_network_id
            }]
        }
        self.mox.StubOutWithMock(app.neutron, 'list_networks')
        app.neutron.list_networks(
            name=docker_network_id).AndReturn(fake_list_response)
        self.mox.ReplayAll()

        return neutron_network_id

    @staticmethod
    def _get_fake_subnets(docker_endpoint_id, neutron_network_id,
                          fake_neutron_subnet_v4_id,
                          fake_neutron_subnet_v6_id):
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createSubnet  # noqa
        fake_subnet_response = {
            "subnets": [{
                "name": '-'.join([docker_endpoint_id, '192.168.1.0']),
                "network_id": neutron_network_id,
                "tenant_id": "c1210485b2424d48804aad5d39c61b8f",
                "allocation_pools": [{"start": "192.168.1.2",
                                      "end": "192.168.1.254"}],
                "gateway_ip": "192.168.1.1",
                "ip_version": 4,
                "cidr": "192.168.1.0/24",
                "id": fake_neutron_subnet_v4_id,
                "enable_dhcp": True
            }, {
                "name": '-'.join([docker_endpoint_id, 'fe80::']),
                "network_id": neutron_network_id,
                "tenant_id": "c1210485b2424d48804aad5d39c61b8f",
                "allocation_pools": [{"start": "fe80::f816:3eff:fe20:57c4",
                                      "end": "fe80::ffff:ffff:ffff:ffff"}],
                "gateway_ip": "fe80::f816:3eff:fe20:57c3",
                "ip_version": 6,
                "cidr": "fe80::/64",
                "id": fake_neutron_subnet_v6_id,
                "enable_dhcp": True
            }]
        }
        return fake_subnet_response

    @staticmethod
    def _get_fake_port(docker_endpoint_id, neutron_network_id,
                       fake_neutron_port_id,
                       fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id):
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createPort  # noqa
        fake_port = {
            'port': {
                "status": "DOWN",
                "name": '-'.join([docker_endpoint_id, '0', 'port']),
                "allowed_address_pairs": [],
                "admin_state_up": True,
                "network_id": neutron_network_id,
                "tenant_id": "d6700c0c9ffa4f1cb322cd4a1f3906fa",
                "device_owner": "",
                "mac_address": "fa:16:3e:20:57:c3",
                "fixed_ips": [{
                    "subnet_id": fake_neutron_subnet_v4_id,
                    "ip_address": "192.168.1.2"
                }, {
                    "subnet_id": fake_neutron_subnet_v6_id,
                    "ip_address": "fe80::f816:3eff:fe20:57c4"
                }],
                "id": fake_neutron_port_id,
                "security_groups": [],
                "device_id": ""
            }
        }
        return fake_port

    @classmethod
    def _get_fake_ports(cls, docker_endpoint_id, neutron_network_id,
                        fake_neutron_port_id,
                        fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id):
        fake_port = cls._get_fake_port(
            docker_endpoint_id, neutron_network_id,
            fake_neutron_port_id,
            fake_neutron_subnet_v4_id, fake_neutron_subnet_v6_id)
        fake_port = fake_port['port']
        fake_ports = {
            'ports': [
                fake_port
            ]
        }

        return fake_ports


class TestKuryrFailures(TestKuryrBase):
    """Unitests for checking if Kuryr handles the failures appropriately."""
