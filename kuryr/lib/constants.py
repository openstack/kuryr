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


PORT_STATUS_ACTIVE = 'ACTIVE'
PORT_STATUS_DOWN = 'DOWN'

DEVICE_OWNER = 'kuryr:container'
NIC_NAME_LEN = 14
VETH_PREFIX = 'tap'
CONTAINER_VETH_PREFIX = 't_c'

# For VLAN type segmentation
MIN_VLAN_TAG = 1
MAX_VLAN_TAG = 4094

BINDING_SUBCOMMAND = 'bind'
DEFAULT_NETWORK_MTU = 1500
FALLBACK_VIF_TYPE = 'unbound'
UNBINDING_SUBCOMMAND = 'unbind'
VIF_DETAILS_KEY = 'binding:vif_details'
VIF_TYPE_KEY = 'binding:vif_type'
