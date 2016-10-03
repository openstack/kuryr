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

from oslo_config import cfg
from oslotest import base

from kuryr.lib import config
from kuryr.lib import constants as const


class TestCase(base.BaseTestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        super(TestCase, self).setUp()
        CONF = cfg.CONF
        CONF.register_opts(config.core_opts)
        CONF.register_opts(config.binding_opts, group=config.binding_group)
        config.register_neutron_opts(CONF)

    @staticmethod
    def _get_fake_networks(neutron_network_id):
        fake_networks_response = {
            "networks": [{
                "status": "ACTIVE",
                "subnets": [],
                "name": "fake_network",
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": neutron_network_id
            }]
        }
        return fake_networks_response

    @staticmethod
    def _get_fake_subnets(docker_endpoint_id, neutron_network_id,
                          fake_neutron_subnet_v4_id,
                          fake_neutron_subnet_v6_id):
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createSubnet  # noqa
        fake_subnet_response = {
            "subnets": [
                {"name": '-'.join([docker_endpoint_id, '192.168.1.0']),
                "network_id": neutron_network_id,
                "tenant_id": "c1210485b2424d48804aad5d39c61b8f",
                "allocation_pools": [{"start": "192.168.1.2",
                                      "end": "192.168.1.254"}],
                "gateway_ip": "192.168.1.1",
                "ip_version": 4,
                "cidr": "192.168.1.0/24",
                "id": fake_neutron_subnet_v4_id,
                "enable_dhcp": True,
                "subnetpool_id": ''},
                {"name": '-'.join([docker_endpoint_id, 'fe80::']),
                "network_id": neutron_network_id,
                "tenant_id": "c1210485b2424d48804aad5d39c61b8f",
                "allocation_pools": [{"start": "fe80::f816:3eff:fe20:57c4",
                                      "end": "fe80::ffff:ffff:ffff:ffff"}],
                "gateway_ip": "fe80::f816:3eff:fe20:57c3",
                "ip_version": 6,
                "cidr": "fe80::/64",
                "id": fake_neutron_subnet_v6_id,
                "enable_dhcp": True,
                "subnetpool_id": ''}
            ]
        }
        return fake_subnet_response

    @staticmethod
    def _get_fake_port(docker_endpoint_id, neutron_network_id,
                       neutron_port_id,
                       neutron_port_status=const.PORT_STATUS_DOWN,
                       neutron_subnet_v4_id=None,
                       neutron_subnet_v6_id=None,
                       neutron_subnet_v4_address="192.168.1.2",
                       neutron_subnet_v6_address="fe80::f816:3eff:fe20:57c4"):
        # The following fake response is retrieved from the Neutron doc:
        #   http://developer.openstack.org/api-ref-networking-v2.html#createPort  # noqa
        fake_port = {
            'port': {
                "status": neutron_port_status,
                "name": docker_endpoint_id + '-port',
                "allowed_address_pairs": [],
                "admin_state_up": True,
                "network_id": neutron_network_id,
                "tenant_id": "d6700c0c9ffa4f1cb322cd4a1f3906fa",
                "device_owner": "",
                "mac_address": "fa:16:3e:20:57:c3",
                "fixed_ips": [],
                "id": neutron_port_id,
                "security_groups": [],
                "device_id": ""
            }
        }

        if neutron_subnet_v4_id:
            fake_port['port']['fixed_ips'].append({
                "subnet_id": neutron_subnet_v4_id,
                "ip_address": neutron_subnet_v4_address
            })
        if neutron_subnet_v6_id:
            fake_port['port']['fixed_ips'].append({
                "subnet_id": neutron_subnet_v6_id,
                "ip_address": neutron_subnet_v6_address
            })
        return fake_port
