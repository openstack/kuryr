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

from ddt import ddt, data, unpack
from oslo_serialization import jsonutils

from kuryr import app
from kuryr.constants import SCHEMA
from kuryr.tests.base import TestKuryrBase


@ddt
class TestKuryr(TestKuryrBase):
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
    @data(('/Plugin.Activate', SCHEMA['PLUGIN_ACTIVATE']),
        ('/NetworkDriver.CreateEndpoint', SCHEMA['CREATE_ENDPOINT']),
        ('/NetworkDriver.EndpointOperInfo', SCHEMA['ENDPOINT_OPER_INFO']),
        ('/NetworkDriver.DeleteEndpoint', SCHEMA['SUCCESS']),
        ('/NetworkDriver.Join', SCHEMA['JOIN']),
        ('/NetworkDriver.Leave', SCHEMA['SUCCESS']))
    @unpack
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
        self.assertEqual(SCHEMA['SUCCESS'], decoded_json)

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
        self.assertEqual(SCHEMA['SUCCESS'], decoded_json)
