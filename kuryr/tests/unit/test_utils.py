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

import uuid

import ddt

from oslo_config import cfg

from kuryr.lib import constants as const
from kuryr.lib import utils
from kuryr.tests.unit import base


@ddt.ddt
class TestKuryrUtils(base.TestCase):
    """Unit tests for utilities."""

    def test_get_veth_pair_names(self):
        fake_neutron_port_id = str(uuid.uuid4())
        generated_ifname, generated_peer = utils.get_veth_pair_names(
            fake_neutron_port_id)

        namelen = const.NIC_NAME_LEN
        ifname_postlen = namelen - len(const.VETH_PREFIX)
        peer_postlen = namelen - len(const.CONTAINER_VETH_PREFIX)

        self.assertEqual(namelen, len(generated_ifname))
        self.assertEqual(namelen, len(generated_peer))
        self.assertIn(const.VETH_PREFIX, generated_ifname)
        self.assertIn(const.CONTAINER_VETH_PREFIX, generated_peer)
        self.assertIn(fake_neutron_port_id[:ifname_postlen], generated_ifname)
        self.assertIn(fake_neutron_port_id[:peer_postlen], generated_peer)

    def test_get_subnetpool_name(self):
        fake_subnet_cidr = "10.0.0.0/16"
        generated_neutron_subnetpool_name = utils.get_neutron_subnetpool_name(
            fake_subnet_cidr)
        name_prefix = cfg.CONF.subnetpool_name_prefix
        self.assertIn(name_prefix, generated_neutron_subnetpool_name)
        self.assertIn(fake_subnet_cidr, generated_neutron_subnetpool_name)
