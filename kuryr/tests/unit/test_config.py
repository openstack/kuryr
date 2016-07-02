#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os


from kuryr.lib import config
from kuryr.tests.unit import base


class ConfigurationTest(base.TestCase):

    def test_defaults(self):
        basepath = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '../../../'))
        self.assertEqual(basepath,
                         config.CONF.pybasedir)
        self.assertEqual(basepath + '/usr/libexec/kuryr',
                         config.CONF.bindir)
        self.assertEqual('http://127.0.0.1:2377',
                         config.CONF.kuryr_uri)

        self.assertEqual('http://127.0.0.1:9696',
                         config.CONF.neutron_client.neutron_uri)

        self.assertEqual('kuryr',
                         config.CONF.neutron_client.default_subnetpool_v4)

        self.assertEqual('kuryr6',
                         config.CONF.neutron_client.default_subnetpool_v6)

        self.assertEqual('http://127.0.0.1:35357/v2.0',
                         config.CONF.keystone_client.auth_uri)
