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

from flask import jsonify

from kuryr import app


# NEXTHOP indicates a StaticRoute with an IP next hop.
NEXTHOP = 0
# CONNECTED indicates a StaticRoute with a interface for directly connected
# peers.
CONNECTED = 1


@app.route('/Plugin.Activate', methods=['POST'])
def plubin_activate():
    return jsonify({"Implements": ["NetworkDriver"]})


@app.route('/NetworkDriver.CreateNetwork', methods=['POST'])
def network_driver_create_network():
    return jsonify({})


@app.route('/NetworkDriver.DeleteNetwork', methods=['POST'])
def network_driver_delete_network():
    return jsonify({})


@app.route('/NetworkDriver.CreateEndpoint', methods=['POST'])
def network_driver_create_endpoint():
    # TODO(tfukushima): This is mocked and should be replaced with real data.
    return jsonify({
        "Interfaces": [{
            "ID": 1,
            "Address": "192.168.1.42/24",
            "AddressIPv6": "fe80::f816:3eff:fe20:57c3/64",
            "MacAddress": "fa:16:3e:20:57:c3",
        }]
    })


@app.route('/NetworkDriver.EndpointOperInfo', methods=['POST'])
def network_driver_endpoint_operational_info():
    # TODO(tfukushima): This is mocked and should be replaced with real data.
    return jsonify({"Value": {}})


@app.route('/NetworkDriver.DeleteEndpoint', methods=['POST'])
def network_driver_delete_endpoint():
    return jsonify({})


@app.route('/NetworkDriver.Join', methods=['POST'])
def network_driver_join():
    # TODO(tfukushima): This is mocked and should be replaced with real data.
    return jsonify({
        "InterfaceNames": [{
            "SrcName": "foobar",
            "DstPrefix": ""
        }],
        "Gateway": "192.168.1.1/24",
        "GatewayIPv6": "fe80::f816:3eff:fe20:57c1/64",
        "StaticRoutes": [{
            "Destination": "192.168.1.42",
            "RouteType": CONNECTED,
            "NextHop": "",
            "InterfaceID": 0
        }]
    })


@app.route('/NetworkDriver.Leave', methods=['POST'])
def network_driver_leave():
    return jsonify({})
