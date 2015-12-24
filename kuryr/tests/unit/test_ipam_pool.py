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

import ddt
from neutronclient.common import exceptions
from oslo_serialization import jsonutils

from kuryr import app
from kuryr.tests.unit import base
from kuryr import utils


@ddt.ddt
class TestIpamRequestPoolFailures(base.TestKuryrFailures):
    """Unit tests for testing request pool failures.

    This test covers error responses listed in the spec:
        http://developer.openstack.org/api-ref-networking-v2-ext.html#createSubnetPool
        http://developer.openstack.org/api-ref-networking-v2-ext.html#listSubnetPools
    """
    def _invoke_create_request(self, pool):
        fake_request = {
            'AddressSpace': '',
            'Pool': pool,
            'SubPool': '',  # In the case --ip-range is not given
            'Options': {},
            'V6': False
        }
        response = self.app.post('/IpamDriver.RequestPool',
                                 content_type='application/json',
                                 data=jsonutils.dumps(fake_request))
        return response

    @ddt.data(exceptions.Unauthorized, exceptions.Forbidden,
              exceptions.NotFound)
    def test_request_pool_create_failures(self, GivenException):
        pool_name = utils.get_neutron_subnetpool_name("10.0.0.0/16")
        new_subnetpool = {
            'name': pool_name,
            'default_prefixlen': 16,
            'prefixes': ['10.0.0.0/16']}

        self.mox.StubOutWithMock(app.neutron, 'list_subnetpools')
        fake_name = pool_name
        app.neutron.list_subnetpools(name=fake_name).AndReturn(
            {'subnetpools': []})

        self.mox.StubOutWithMock(app.neutron, 'create_subnetpool')
        app.neutron.create_subnetpool(
            {'subnetpool': new_subnetpool}).AndRaise(GivenException)

        self.mox.ReplayAll()

        pool = '10.0.0.0/16'
        response = self._invoke_create_request(pool)

        self.assertEqual(GivenException.status_code, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        self.assertEqual(
            {'Err': GivenException.message}, decoded_json)

    def test_request_pool_bad_request_failure(self):
        pool = 'pool-should-be-cidr'
        response = self._invoke_create_request(pool)

        self.assertEqual(400, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertIn('Err', decoded_json)
        self.assertIn(pool, decoded_json['Err'])
        self.assertIn('Pool', decoded_json['Err'])

    def test_request_pool_list_subnetpool_failure(self):
        self.mox.StubOutWithMock(app.neutron, 'list_subnetpools')
        pool_name = utils.get_neutron_subnetpool_name("10.0.0.0/16")
        fake_name = pool_name
        ex = exceptions.Unauthorized
        app.neutron.list_subnetpools(name=fake_name).AndRaise(ex)

        self.mox.ReplayAll()

        pool = '10.0.0.0/16'
        response = self._invoke_create_request(pool)

        self.assertEqual(ex.status_code, response.status_code)
