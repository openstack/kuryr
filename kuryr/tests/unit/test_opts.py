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

import mock

from kuryr.lib import opts as kuryr_opts
from kuryr.tests.unit import base


class OptsTest(base.TestCase):

    _fake_kuryr_opts = [(None, 'fakevalue1'), ('Key1', 'fakevalue2')]
    _fake_neutron_opts = [('poolv4', 'swimming4'), ('poolv6', 'swimming6')]
    _fake_binding_group = 'binding_group'
    _fake_binding_opts = [('driver', 'my.ipvlan')]

    @mock.patch.multiple(kuryr_opts.config,
                         binding_group=_fake_binding_group,
                         binding_opts=_fake_binding_opts)
    @mock.patch.multiple(kuryr_opts,
                         _kuryr_opts=_fake_kuryr_opts,
                         list_neutron_opts=mock.DEFAULT)
    def test_list_kuryr_opts(self, list_neutron_opts):
        list_neutron_opts.return_value = self._fake_neutron_opts

        self.assertEqual(self._fake_kuryr_opts + self._fake_neutron_opts +
                         [(self._fake_binding_group, self._fake_binding_opts)],
                         kuryr_opts.list_kuryr_opts())
