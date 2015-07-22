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

from ddt import ddt, data, unpack
from oslo_serialization import jsonutils

from kuryr.constants import SCHEMA
from kuryr.tests import base


@ddt
class TestKuryr(base.TestCase):
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
        ('/NetworkDriver.CreateNetwork', SCHEMA['SUCCESS']),
        ('/NetworkDriver.DeleteNetwork', SCHEMA['SUCCESS']),
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
