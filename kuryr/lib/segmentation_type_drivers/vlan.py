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
from six import moves

from kuryr.lib import constants as const
from kuryr.lib import exceptions


class SegmentationDriver(object):
    def __init__(self):
        self.available_local_vlans = set(moves.range(const.MIN_VLAN_TAG,
                                                 const.MAX_VLAN_TAG + 1))

    def allocate_segmentation_id(self, allocated_ids=set()):
        self.available_local_vlans.difference_update(allocated_ids)
        try:
            allocated = self.available_local_vlans.pop()
        except KeyError:
            raise exceptions.segmentationIdAllocationFailure

        return allocated

    def release_segmentation_id(self, id):
        self.available_local_vlans.add(id)
