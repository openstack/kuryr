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

from kuryr.schemata import endpoint_create
from kuryr.schemata import endpoint_delete
from kuryr.schemata import join
from kuryr.schemata import leave
from kuryr.schemata import network_create
from kuryr.schemata import network_delete
from kuryr.schemata import release_address
from kuryr.schemata import release_pool
from kuryr.schemata import request_address
from kuryr.schemata import request_pool


# Aliases for schemata in each module
ENDPOINT_CREATE_SCHEMA = endpoint_create.ENDPOINT_CREATE_SCHEMA
ENDPOINT_DELETE_SCHEMA = endpoint_delete.ENDPOINT_DELETE_SCHEMA
JOIN_SCHEMA = join.JOIN_SCHEMA
LEAVE_SCHEMA = leave.LEAVE_SCHEMA
NETWORK_CREATE_SCHEMA = network_create.NETWORK_CREATE_SCHEMA
NETWORK_DELETE_SCHEMA = network_delete.NETWORK_DELETE_SCHEMA
RELEASE_ADDRESS_SCHEMA = release_address.RELEASE_ADDRESS_SCHEMA
RELEASE_POOL_SCHEMA = release_pool.RELEASE_POOL_SCHEMA
REQUEST_ADDRESS_SCHEMA = request_address.REQUEST_ADDRESS_SCHEMA
REQUEST_POOL_SCHEMA = request_pool.REQUEST_POOL_SCHEMA
