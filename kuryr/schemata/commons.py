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

COMMONS = {
    u'description': u'Common data schemata shared among other schemata.',
    u'links': [],
    u'title': u'Kuryr Common Data Schema Definitions',
    u'properties': {
        u'options': {u'$ref': u'/schemata/commons#/definitions/options'},
        u'mac': {u'$ref': u'/schemata/commons#/definitions/mac'},
        u'cidrv6': {u'$ref': u'/schemata/commons#/definitions/cidrv6'},
        u'interface': {u'$ref': u'/schemata/commons#/definitions/interface'},
        u'cidr': {u'$ref': u'/schemata/commons#/definitions/cidr'},
        u'id': {u'$ref': u'/schemata/commons#/definitions/id'}
    },
    u'definitions': {
        u'options': {
            u'type': [u'object', u'null'],
            u'description': u'Options.',
            u'example': {}
        },
        u'mac': {
            u'pattern': (u'^((?:[0-9a-f]{2}:){5}[0-9a-f]{2}|'
                         u'(?:[0-9A-F]{2}:){5}[0-9A-F]{2})$'),
            u'type': u'string',
            u'description': u'A MAC address.',
            u'example': u'aa:bb:cc:dd:ee:ff'
        },
        u'cidrv6': {
            u'pattern': (u'^(('
                u'([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|'
                u'([0-9a-fA-F]{1,4}:){1,7}:|'
                u'([0-9a-fA-F]{1,4}:){1,6}\:[0-9a-fA-F]{1,4}|'
                u'([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|'
                u'([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|'
                u'([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|'
                u'([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|'
                u'[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|'
                u':((:[0-9a-fA-F]{1,4}){1,7}|:)|'
                u'fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|'
                u'::(ffff(:0{1,4}){0,1}:){0,1}'
                u'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\\.){3,3}'
                u'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|'
                u'([0-9a-fA-F]{1,4}:){1,4}:'
                u'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\\.){3,3}'
                u'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
                u'(/(1[0-2][0-8]|[1-9]?[0-9])))$'),
            u'type': u'string',
            u'description': u'A IPv6 CIDR of the subnet'
        },
        u'interface': {
            u'properties': {
                u'ID': {
                    u'description': u'Index of the interface',
                    u'type': u'number',
                },
                u'AddressIPv6': {
                    u'description': u'IPv6 CIDR',
                    u'$ref': u'#/definitions/commons/definitions/cidrv6'
                },
                u'MacAddress': {
                    u'description': u'MAC address',
                    u'$ref': u'#/definitions/commons/definitions/mac'
                },
                u'Address': {
                    u'description': u'IPv4 CIDR',
                    u'$ref': u'#/definitions/commons/definitions/cidr'
                }
            },
            u'type': [u'object', u'null'],
            u'description': u'Interface used in requests against Endpoints.',
            u'example': {
                u'AddressIPv6': u'fe80::f816:3eff:fe20:57c3/64',
                u'MacAddress': u'fa:16:3e:20:57:c3',
                u'Address': u'192.168.1.42/24'
            }
        },
        u'cidr': {
            u'pattern': (u'^((25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])\\.){3}'
                         u'(25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])'
                         u'/(3[0-2]|((1|2)?[0-9]))$'),
            u'type': u'string',
            u'description': u'A IPv4 CIDR of the subnet.',
            u'example': u'10.0.0.0/24'
        },
        u'id': {
            u'pattern': u'^([0-9a-f]{64})$',
            u'type': u'string',
            u'description': u'256 bits ID value of Docker.',
            u'example':
            u'51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1'
        },
        u'sandbox_key': {
            u'pattern': u'^(/var/run/docker/netns/[0-9a-f]{12})$',
            u'type': u'string',
            u'description': u'Sandbox information of netns.',
            u'example': '/var/run/docker/netns/12bbda391ed0'
        }
    },
    u'$schema': u'http://json-schema.org/draft-04/hyper-schema',
    u'type': u'object',
    u'id': u'schemata/commons'
}
