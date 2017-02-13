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
import random

from six import moves

from kuryr.lib import constants as const
from kuryr.lib import exceptions

DEFAULT_MAX_RETRY_COUNT = 3


class SegmentationDriver(object):
    def __init__(self):
        self.available_local_vlans = set(moves.range(const.MIN_VLAN_TAG,
                                                     const.MAX_VLAN_TAG + 1))

    def allocate_segmentation_id(self, allocated_ids=set()):
        self.available_local_vlans.difference_update(allocated_ids)
        for i in range(DEFAULT_MAX_RETRY_COUNT):
            try:
                allocated = random.choice(list(self.available_local_vlans))
                self.available_local_vlans.remove(allocated)
                return allocated
            except IndexError:
                raise exceptions.SegmentationIdAllocationFailure(
                    'There are no vlan ids available.')
            except KeyError:
                # Other thread obtained the same vlan_id, so a new try is
                # needed
                continue
        raise exceptions.SegmentationIdAllocationFailure(
            'Max number of retries reached without '
            'finding an available vlan id.')

    def release_segmentation_id(self, id):
        self.available_local_vlans.add(id)
