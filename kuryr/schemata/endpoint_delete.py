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

ENDPOINT_DELETE_SCHEMA = {
    u'links': [{
        u'method': u'POST',
        u'href': u'/NetworkDriver.DeleteEndpoint',
        u'description': u'Delete an Endpoint',
        u'rel': u'self',
        u'title': u'Delete'
    }],
    u'title': u'Delete endpoint',
    u'required': [u'NetworkID', u'EndpointID'],
    u'definitions': {u'commons': {}},
    u'$schema': u'http://json-schema.org/draft-04/hyper-schema',
    u'type': u'object',
    u'properties': {
        u'NetworkID': {
            u'description': u'Network ID',
            u'$ref': u'#/definitions/commons/definitions/id'
        },
        u'EndpointID': {
            u'description': u'Endpoint ID',
            u'$ref': u'#/definitions/commons/definitions/id'
        }
    }
}

ENDPOINT_DELETE_SCHEMA[u'definitions'][u'commons'] = commons.COMMONS
