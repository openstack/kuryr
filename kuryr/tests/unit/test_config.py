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

from oslo_config import cfg

from kuryr.lib import config as kuryr_config
from kuryr.tests.unit import base


class ConfigurationTest(base.TestCase):

    def test_defaults(self):
        neutron_group = getattr(cfg.CONF, kuryr_config.neutron_group.name)
        self.assertEqual('kuryr',
                         neutron_group.default_subnetpool_v4)

        self.assertEqual('kuryr6',
                         neutron_group.default_subnetpool_v6)
        self.assertEqual('public',
                         neutron_group.endpoint_type)
        self.assertEqual('baremetal',
                         cfg.CONF.deployment_type)
        self.assertEqual('kuryr.lib.binding.drivers.veth',
                         cfg.CONF.binding.driver)
