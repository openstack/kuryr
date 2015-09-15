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

import ddt

from kuryr.tests import base
from kuryr import utils


@ddt.ddt
class TestKuryrUtils(base.TestKuryrBase):
    """Unit tests for utilities."""

    @ddt.data(hashlib.sha256(str(random.getrandbits(256))).hexdigest(),
          '51c75a2515d4' '51c75a')
    def test_get_sandbox_key(self, fake_container_id):
        sandbox_key = utils.get_sandbox_key(fake_container_id)
        expected = '/'.join([utils.DOCKER_NETNS_BASE, fake_container_id[:12]])
        self.assertEqual(expected, sandbox_key)
