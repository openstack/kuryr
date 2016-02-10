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

import ddt
from oslo_config import cfg

from kuryr.tests.unit import base
from kuryr import utils


@ddt.ddt
class TestKuryrUtils(base.TestKuryrBase):
    """Unit tests for utilities."""

    @ddt.data(hashlib.sha256(utils.getrandbits(
        256)).hexdigest(), '51c75a2515d4' '51c75a')
    def test_get_sandbox_key(self, fake_container_id):
        sandbox_key = utils.get_sandbox_key(fake_container_id)
        expected = '/'.join([utils.DOCKER_NETNS_BASE, fake_container_id[:12]])
        self.assertEqual(expected, sandbox_key)

    def test_get_port_name(self):
        fake_docker_endpoint_id = hashlib.sha256(
            utils.getrandbits(256)).hexdigest()
        generated_neutron_port_name = utils.get_neutron_port_name(
            fake_docker_endpoint_id)
        self.assertIn(utils.PORT_POSTFIX, generated_neutron_port_name)
        self.assertIn(fake_docker_endpoint_id, generated_neutron_port_name)

    def test_get_subnetpool_name(self):
        fake_subnet_cidr = "10.0.0.0/16"
        generated_neutron_subnetpool_name = utils.get_neutron_subnetpool_name(
            fake_subnet_cidr)
        name_prefix = cfg.CONF.subnetpool_name_prefix
        self.assertIn(name_prefix, generated_neutron_subnetpool_name)
        self.assertIn(fake_subnet_cidr, generated_neutron_subnetpool_name)

    def test_get_dict_format_fixed_ips_from_kv_format(self):
        fake_fixed_ips_kv_format = \
            ['subnet_id=5083bda8-1b7c-4625-97f3-1d4c33bfeea8',
             'ip_address=192.168.1.2',
             'subnet_id=6607a230-f3eb-4937-b09f-9dd659211139',
             'ip_address=fdfa:8456:1afa:0:f816:3eff:fe67:885e']
        expected_dict_form = \
            [{'subnet_id': '5083bda8-1b7c-4625-97f3-1d4c33bfeea8',
              'ip_address': '192.168.1.2'},
             {'subnet_id': '6607a230-f3eb-4937-b09f-9dd659211139',
              'ip_address': 'fdfa:8456:1afa:0:f816:3eff:fe67:885e'}]
        fixed_ips = utils.get_dict_format_fixed_ips_from_kv_format(
                        fake_fixed_ips_kv_format)
        self.assertEqual(expected_dict_form, fixed_ips)
