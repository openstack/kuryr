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
import uuid

from ddt import ddt
from oslo_serialization import jsonutils

from kuryr import app
from kuryr.common import constants as const
from kuryr.tests.unit import base
from kuryr import utils


@ddt
class TestKuryrNetworkPreExisting(base.TestKuryrBase):

    def _ids(self):
        docker_network_id = hashlib.sha256(
            utils.getrandbits(256)).hexdigest()
        fake_neutron_net_id = "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
        fake_response = {
            'networks':
            [
                {
                    "status": "ACTIVE",
                    "subnets": [],
                    "admin_state_up": True,
                    "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                    "router:external": False,
                    "segments": [],
                    "shared": False,
                    "id": fake_neutron_net_id
                }
            ]
        }
        return docker_network_id, fake_neutron_net_id, fake_response

    def test_create_network_pre_existing(self):
        docker_network_id, fake_neutron_net_id, fake_response = self._ids()

        self.mox.StubOutWithMock(app.neutron, "list_networks")
        app.neutron.list_networks(id=fake_neutron_net_id).AndReturn(
            fake_response)

        self.mox.StubOutWithMock(app.neutron, "add_tag")
        tags = utils.create_net_tags(docker_network_id)
        for tag in tags:
            app.neutron.add_tag('networks', fake_neutron_net_id, tag)
        app.neutron.add_tag('networks', fake_neutron_net_id,
                            const.KURYR_EXISTING_NEUTRON_NET)

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
                const.NETWORK_GENERIC_OPTIONS: {
                    const.NEUTRON_UUID_OPTION: fake_neutron_net_id
                }
            }
        }
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(network_request))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(const.SCHEMA['SUCCESS'], decoded_json)

    def test_delete_network_pre_existing(self):
        docker_network_id, fake_neutron_net_id, fake_response = self._ids()

        self.mox.StubOutWithMock(app.neutron, 'list_networks')
        t = utils.make_net_tags(docker_network_id)
        te = t + ',' + const.KURYR_EXISTING_NEUTRON_NET
        app.neutron.list_networks(tags=te).AndReturn(
            fake_response)

        self.mox.StubOutWithMock(app.neutron, "remove_tag")
        tags = utils.create_net_tags(docker_network_id)
        for tag in tags:
            app.neutron.remove_tag('networks', fake_neutron_net_id, tag)
        app.neutron.remove_tag('networks', fake_neutron_net_id,
                               const.KURYR_EXISTING_NEUTRON_NET)

        self.mox.ReplayAll()
        data = {'NetworkID': docker_network_id}
        response = self.app.post('/NetworkDriver.DeleteNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        self.assertEqual(200, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertEqual(const.SCHEMA['SUCCESS'], decoded_json)
