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

from ddt import data
from ddt import ddt
from neutronclient.common import exceptions
from oslo_serialization import jsonutils

from kuryr import app
from kuryr.tests import base


class TestKuryrNetworkCreateFailures(base.TestKuryrFailures):
    """Unittests for the failures for creating networks.

    This test covers error responses listed in the spec:
      http://developer.openstack.org/api-ref-networking-v2-ext.html#createProviderNetwork  # noqa
    """

    def _create_network_with_exception(self, network_name, ex):
        self.mox.StubOutWithMock(app.neutron, "create_network")
        fake_request = {
            "network": {
                "name": network_name,
                "admin_state_up": True
            }
        }
        app.neutron.create_network(fake_request).AndRaise(ex)
        self.mox.ReplayAll()

    def _invoke_create_request(self, network_name):
        data = {'NetworkID': network_name, 'Options': {}}
        response = self.app.post('/NetworkDriver.CreateNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))
        return response

    def test_create_network_unauthorized(self):
        docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        self._create_network_with_exception(
            docker_network_id, exceptions.Unauthorized())

        response = self._invoke_create_request(docker_network_id)

        self.assertEqual(401, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertTrue('Err' in decoded_json)
        self.assertEqual(
            {'Err': exceptions.Unauthorized.message}, decoded_json)


@ddt
class TestKuryrNetworkDeleteFailures(base.TestKuryrFailures):
    """Unittests for the failures for deleting networks.

    This test covers error responses listed in the spec:
      http://developer.openstack.org/api-ref-networking-v2-ext.html#deleteProviderNetwork  # noqa
    """
    def _delete_network_with_exception(self, network_id, ex):
        fake_neutron_network_id = "4e8e5957-649f-477b-9e5b-f1f75b21c03c"
        fake_networks_response = {
            "networks": [{
                "status": "ACTIVE",
                "subnets": [],
                "name": network_id,
                "admin_state_up": True,
                "tenant_id": "9bacb3c5d39d41a79512987f338cf177",
                "router:external": False,
                "segments": [],
                "shared": False,
                "id": fake_neutron_network_id
            }]
        }
        self.mox.StubOutWithMock(app.neutron, 'list_networks')
        app.neutron.list_networks(
            name=network_id).AndReturn(fake_networks_response)
        self.mox.StubOutWithMock(app.neutron, 'delete_network')
        app.neutron.delete_network(fake_neutron_network_id).AndRaise(ex)
        self.mox.ReplayAll()

    def _invoke_delete_request(self, network_name):
        data = {'NetworkID': network_name}
        response = self.app.post('/NetworkDriver.DeleteNetwork',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))
        return response

    @data(exceptions.Unauthorized, exceptions.NotFound, exceptions.Conflict)
    def test_delete_network_failures(self, GivenException):
        docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        self._delete_network_with_exception(
            docker_network_id, GivenException())

        response = self._invoke_delete_request(docker_network_id)

        self.assertEqual(GivenException.status_code, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertTrue('Err' in decoded_json)
        self.assertEqual({'Err': GivenException.message}, decoded_json)
