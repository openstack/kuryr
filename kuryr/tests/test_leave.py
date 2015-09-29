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

import ddt
from oslo_concurrency import processutils
from oslo_serialization import jsonutils
from werkzeug import exceptions as w_exceptions

from kuryr import app
from kuryr import binding
from kuryr.common import exceptions
from kuryr.tests import base
from kuryr import utils


@ddt.ddt
class TestKuryrLeaveFailures(base.TestKuryrFailures):
    """Unit tests for the failures for unbinding a Neutron port.
    """
    def _invoke_leave_request(self, docker_network_id,
                              docker_endpoint_id):
        data = {
            'NetworkID': docker_network_id,
            'EndpointID': docker_endpoint_id,
        }
        response = self.app.post('/NetworkDriver.Leave',
                                 content_type='application/json',
                                 data=jsonutils.dumps(data))

        return response

    def _port_unbind_with_exception(self, docker_endpoint_id,
                                    neutron_port, ex):
        fake_unbinding_response = ('fake stdout', '')
        self.mox.StubOutWithMock(binding, 'port_unbind')
        if ex:
            binding.port_unbind(docker_endpoint_id, neutron_port).AndRaise(ex)
        else:
            binding.port_unbind(docker_endpoint_id, neutron_port).AndReturn(
                fake_unbinding_response)
        self.mox.ReplayAll()

        return fake_unbinding_response

    @ddt.data(exceptions.VethDeletionFailure,
              processutils.ProcessExecutionError)
    def test_leave_unbinding_failure(self, GivenException):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        fake_docker_endpoint_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()

        fake_neutron_network_id = str(uuid.uuid4())
        self._mock_out_network(fake_neutron_network_id, fake_docker_network_id)
        fake_neutron_port_id = str(uuid.uuid4())
        self.mox.StubOutWithMock(app.neutron, 'list_ports')
        neutron_port_name = utils.get_neutron_port_name(
            fake_docker_endpoint_id)
        fake_neutron_v4_subnet_id = str(uuid.uuid4())
        fake_neutron_v6_subnet_id = str(uuid.uuid4())
        fake_neutron_ports_response = self._get_fake_ports(
            fake_docker_endpoint_id, fake_neutron_network_id,
            fake_neutron_port_id,
            fake_neutron_v4_subnet_id, fake_neutron_v6_subnet_id)
        app.neutron.list_ports(name=neutron_port_name).AndReturn(
            fake_neutron_ports_response)
        fake_neutron_port = fake_neutron_ports_response['ports'][0]

        fake_message = "fake message"
        fake_exception = GivenException(fake_message)
        self._port_unbind_with_exception(
            fake_docker_endpoint_id, fake_neutron_port, fake_exception)

        response = self._invoke_leave_request(
            fake_docker_network_id, fake_docker_endpoint_id)

        self.assertEqual(
            w_exceptions.InternalServerError.code, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertTrue('Err' in decoded_json)
        self.assertTrue(fake_message in decoded_json['Err'])

    def test_leave_bad_request(self):
        fake_docker_network_id = hashlib.sha256(
            str(random.getrandbits(256))).hexdigest()
        invalid_docker_endpoint_id = 'id-should-be-hexdigits'

        response = self._invoke_leave_request(
            fake_docker_network_id, invalid_docker_endpoint_id)

        self.assertEqual(w_exceptions.BadRequest.code, response.status_code)
        decoded_json = jsonutils.loads(response.data)
        self.assertTrue('Err' in decoded_json)
        # TODO(tfukushima): Add the better error message validation.
        self.assertTrue(invalid_docker_endpoint_id in decoded_json['Err'])
        self.assertTrue('EndpointID' in decoded_json['Err'])
