# Copyright 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

from oslo_config import cfg
from six import moves

from kuryr.lib import constants as const
from kuryr.lib import exceptions
from kuryr.tests.unit import base

from kuryr.lib.segmentation_type_drivers import vlan


class VlanSegmentationDriverTest(base.TestCase):
    """Unit tests for VLAN segmentation driver."""

    def setUp(self):
        super(VlanSegmentationDriverTest, self).setUp()
        cfg.CONF.binding.driver = 'kuryr.lib.binding.drivers.vlan'

    def test_allocate_segmentation_id(self):
        vlan_seg_driver = vlan.SegmentationDriver()
        allocated_ids = set([1, 2, 3])

        vlan_id = vlan_seg_driver.allocate_segmentation_id(allocated_ids)

        self.assertNotIn(vlan_id, vlan_seg_driver.available_local_vlans)
        self.assertNotIn(allocated_ids, vlan_seg_driver.available_local_vlans)

    def test_allocate_segmentation_id_only_1_available(self):
        vlan_seg_driver = vlan.SegmentationDriver()
        allocated_ids = set(moves.range(const.MIN_VLAN_TAG,
                                        const.MAX_VLAN_TAG + 1))
        allocated_ids.remove(const.MAX_VLAN_TAG)

        vlan_id = vlan_seg_driver.allocate_segmentation_id(allocated_ids)

        self.assertNotIn(vlan_id, vlan_seg_driver.available_local_vlans)
        self.assertNotIn(allocated_ids, vlan_seg_driver.available_local_vlans)
        self.assertEqual(vlan_id, const.MAX_VLAN_TAG)

    def test_allocate_segmentation_id_no_allocated_ids(self):
        vlan_seg_driver = vlan.SegmentationDriver()
        vlan_id = vlan_seg_driver.allocate_segmentation_id()
        self.assertNotIn(vlan_id, vlan_seg_driver.available_local_vlans)

    def test_allocate_segmentation_id_no_available_vlans(self):
        vlan_seg_driver = vlan.SegmentationDriver()
        allocated_ids = set(moves.range(const.MIN_VLAN_TAG,
                                        const.MAX_VLAN_TAG + 1))

        self.assertRaises(exceptions.SegmentationIdAllocationFailure,
                          vlan_seg_driver.allocate_segmentation_id,
                          allocated_ids)

    @mock.patch('random.choice')
    def test_allocate_segmentation_id_max_retries(self, mock_choice):
        mock_choice.side_effect = [1, 1, 1]
        vlan_seg_driver = vlan.SegmentationDriver()
        allocated_ids = set([1, 2, 3])

        self.assertRaises(exceptions.SegmentationIdAllocationFailure,
                          vlan_seg_driver.allocate_segmentation_id,
                          allocated_ids)
        self.assertEqual(len(mock_choice.mock_calls), 3)

    @mock.patch('random.choice')
    def test_allocate_segmentation_id_2_retries(self, mock_choice):
        vlan_seg_driver = vlan.SegmentationDriver()
        vlan_seg_driver.available_local_vlans = set(moves.range(1, 10))
        allocated_ids = set([1, 2, 3])
        mock_choice.side_effect = [1, 1, 5]

        vlan_id = vlan_seg_driver.allocate_segmentation_id(allocated_ids)

        self.assertEqual(len(mock_choice.mock_calls), 3)
        self.assertEqual(vlan_id, 5)

    def test_release_segmentation_id(self):
        vlan_seg_driver = vlan.SegmentationDriver()
        vlan_seg_driver.available_local_vlans = set(moves.range(1, 10))
        vlan_id = 20

        vlan_seg_driver.release_segmentation_id(vlan_id)

        self.assertIn(vlan_id, vlan_seg_driver.available_local_vlans)
