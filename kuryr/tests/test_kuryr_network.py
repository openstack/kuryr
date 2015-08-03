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
