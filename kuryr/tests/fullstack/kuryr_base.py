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

import docker

from oslotest import base

from kuryr import controllers


class KuryrBaseTest(base.BaseTestCase):
    """Basic class for Kuryr fullstack testing

    This class has common code shared for Kuryr fullstack testing
    including the various clients (docker, neutron) and common
    setup/cleanup code.
    """
    def setUp(self):
        super(KuryrBaseTest, self).setUp()
        self.docker_client = docker.Client(
            base_url='tcp://0.0.0.0:2375')
        self.neutron_client = controllers.get_neutron_client()
