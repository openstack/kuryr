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

from oslo_config import cfg
from oslo_utils import importutils

from kuryr.lib import binding
from kuryr.lib import exceptions
from kuryr.tests.unit import base


class TestBinding(base.TestCase):
    """Unit tests for binding module"""

    def test__verify_driver(self):
        cfg.CONF.set_override('enabled_drivers',
                              ['kuryr.lib.binding.drivers.veth'],
                              group='binding')
        driver = importutils.import_module('kuryr.lib.binding.drivers.veth')
        binding._verify_driver(driver)  # assert no exception raise
        driver = importutils.import_module('kuryr.lib.binding.drivers.vlan')
        self.assertRaises(exceptions.DriverNotEnabledException,
                          binding._verify_driver, driver)
