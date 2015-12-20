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
import os_client_config

from oslotest import base

from neutronclient.neutron import client


def get_cloud_config(cloud='devstack-admin'):
    return os_client_config.OpenStackConfig().get_one_cloud(cloud=cloud)


def credentials(cloud='devstack-admin'):
    """Retrieves credentials to run functional tests

    Credentials are either read via os-client-config from the environment
    or from a config file ('clouds.yaml'). Environment variables override
    those from the config file.

    devstack produces a clouds.yaml with two named clouds - one named
    'devstack' which has user privs and one named 'devstack-admin' which
    has admin privs. This function will default to getting the devstack-admin
    cloud as that is the current expected behavior.
    """
    return get_cloud_config(cloud=cloud).get_auth_args()


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

        self.creds = credentials()
        username = self.creds['username']
        tenant_name = self.creds['project_name']
        password = self.creds['password']
        auth_url = self.creds['auth_url']
        self.neutron_client = client.Client('2.0', username=username,
                                            tenant_name=tenant_name,
                                            password=password,
                                            auth_url=auth_url)
