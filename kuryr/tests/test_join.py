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

from oslo_serialization import jsonutils

from kuryr.tests import base
from kuryr import utils


class TestKuryrJoinFailures(base.TestKuryrFailures):
    """Unit tests for the failures for binding a Neutron port to an interface.
    """
    def _invoke_join_request(self, docker_network_id,
                             docker_endpoint_id, sandbox_key):
        data = {
            'NetworkID': docker_network_id,
            'EndpointID': docker_endpoint_id,
            'SandboxKey': sandbox_key,
            'Options': {},
        }
        response = self.app.post('/NetworkDriver.Join',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        return response

    def test_join_bad_request(self):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        invalid_docker_endpoint_id = 'id-should-be-hexdigits'
        fake_container_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()

        response = self._invoke_join_request(
            fake_docker_network_id, invalid_docker_endpoint_id,
            utils.get_sandbox_key(fake_container_id))

        self.assertEqual(400, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertTrue('Err' in decoded_json)
        # TODO(tfukushima): Add the better error message validation.
        self.assertTrue(invalid_docker_endpoint_id in decoded_json['Err'])
        self.assertTrue('EndpointID' in decoded_json['Err'])
