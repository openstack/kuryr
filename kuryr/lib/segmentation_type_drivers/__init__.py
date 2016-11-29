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

from kuryr.lib import exceptions as ex

BASE_PATH = 'kuryr.lib.segmentation_type_drivers'

driver_name = cfg.CONF.binding.driver.rsplit('.', 1)[1]

# REVISIT(vikasc): Need to remove this if check
if driver_name == 'vlan':
    seg_driver_path = '.'.join([BASE_PATH, driver_name])
    segmentation_driver = importutils.import_module(seg_driver_path)
    driver = segmentation_driver.SegmentationDriver()


def allocate_segmentation_id(allocated_ids=set()):
    """Allocates a segmentation ID."""
    try:
        id = driver.allocate_segmentation_id(allocated_ids)
    except NameError:
        raise ex.SegmentationDriverBindingDriverCompatibilityFailure
    return id


def release_segmentation_id(id):
    """Releases the segmentation ID."""
    try:
        driver.release_segmentation_id(id)
    except NameError:
        raise ex.SegmentationDriverBindingDriverCompatibilityFailure
