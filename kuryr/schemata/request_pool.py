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

REQUEST_POOL_SCHEMA = {
    u'links': [{
        u'method': u'POST',
        u'href': u'/IpamDriver.RequestPool',
        u'description': u'Allocate pool of ip addresses',
        u'rel': u'self',
        u'title': u'Create'
    }],
    u'title': u'Create pool',
    u'required': [u'AddressSpace', u'Pool', u'SubPool', u'V6'],
    u'definitions': {u'commons': {}},
    u'$schema': u'http://json-schema.org/draft-04/hyper-schema',
    u'type': u'object',
    u'properties': {
        u'AddressSpace': {
            u'description': u'The name of the address space.',
            u'type': u'string',
            u'example': u'foo',
        },
        u'Pool': {
            u'description': u'A range of IP Addresses represented in '
                            u'CIDR format address/mask.',
            u'$ref': u'#/definitions/commons/definitions/cidr'
        },
        u'SubPool': {
            u'description': u'A subset of IP range from Pool in'
                            u'CIDR format address/mask.',
            u'$ref': u'#/definitions/commons/definitions/cidr'
        },
        u'Options': {
            u'type': [u'object', u'null'],
            u'description': u'Options',
            u'example': {},
        },
        u'V6': {
            u'description': u'If set to "True", requesting IPv6 pool and '
                            u'vice-versa.',
            u'type': u'boolean',
            u'example': False
        }
    }
}

REQUEST_POOL_SCHEMA[u'definitions'][u'commons'] = commons.COMMONS
