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

from kuryr.schemata import commons

RELEASE_POOL_SCHEMA = {
    u'links': [{
        u'method': u'POST',
        u'href': u'/IpamDriver.ReleasePool',
        u'description': u'Release an ip pool',
        u'rel': u'self',
        u'title': u'Release'
    }],
    u'title': u'Release an IP pool',
    u'required': [u'PoolID'],
    u'definitions': {u'commons': {}},
    u'$schema': u'http://json-schema.org/draft-04/hyper-schema',
    u'type': u'object',
    u'properties': {
        u'PoolID': {
            u'description': u'neutron ID of allocated subnetpool',
            u'$ref': u'#/definitions/commons/definitions/uuid'
        }
    }
}

RELEASE_POOL_SCHEMA[u'definitions'][u'commons'] = commons.COMMONS
