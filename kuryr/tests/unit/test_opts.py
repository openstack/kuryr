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

    def test_list_kuryr_opts(self):
        fake_kuryr_opts = [(None, 'fakevalue1'),
                           ('Key1', 'fakevalue2')]
        fake_kuryr_opts_mock = mock.PropertyMock(return_value=fake_kuryr_opts)
        with mock.patch.object(kuryr_opts, '_kuryr_opts',
                  new_callable=fake_kuryr_opts_mock):
            self.assertEqual(fake_kuryr_opts, kuryr_opts.list_kuryr_opts())
