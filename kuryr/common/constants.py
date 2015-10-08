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


TYPES = {
    # NEXTHOP indicates a StaticRoute with an IP next hop.
    "NEXTHOP": 0,
    # CONNECTED indicates a StaticRoute with a interface for directly connected
    # peers.
    "CONNECTED": 1
}

SCHEMA = {
    "PLUGIN_ACTIVATE": {"Implements": ["NetworkDriver"]},
    # TODO(tfukushima): This is mocked and should be replaced with real data.
    "CREATE_ENDPOINT": {
        "Interfaces": [{
            "ID": 1,
            "Address": "192.168.1.42/24",
            "AddressIPv6": "fe80::f816:3eff:fe20:57c3/64",
            "MacAddress": "fa:16:3e:20:57:c3",
        }]
    },
    # TODO(tfukushima): This is mocked and should be replaced with real data.
    "ENDPOINT_OPER_INFO": {"Value": {}},
    # TODO(tfukushima): This is mocked and should be replaced with real data.
    "JOIN": {
        "InterfaceNames": [{
            "SrcName": "foobar",
            "DstPrefix": ""
        }],
        "Gateway": "192.168.1.1/24",
        "GatewayIPv6": "fe80::f816:3eff:fe20:57c1/64",
        "StaticRoutes": [{
            "Destination": "192.168.1.42",
            "RouteType": TYPES['CONNECTED'],
            "NextHop": "",
            "InterfaceID": 0
        }]
    },
    "SUCCESS": {}
}

DEVICE_OWNER = 'kuryr:container'
