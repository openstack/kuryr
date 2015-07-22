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
from kuryr.constants import SCHEMA


@app.route('/Plugin.Activate', methods=['POST'])
def plugin_activate():
    return jsonify(SCHEMA['PLUGIN_ACTIVATE'])


@app.route('/NetworkDriver.CreateNetwork', methods=['POST'])
def network_driver_create_network():
    return jsonify(SCHEMA['SUCCESS'])


@app.route('/NetworkDriver.DeleteNetwork', methods=['POST'])
def network_driver_delete_network():
    return jsonify(SCHEMA['SUCCESS'])


@app.route('/NetworkDriver.CreateEndpoint', methods=['POST'])
def network_driver_create_endpoint():
    return jsonify(SCHEMA['CREATE_ENDPOINT'])


@app.route('/NetworkDriver.EndpointOperInfo', methods=['POST'])
def network_driver_endpoint_operational_info():
    return jsonify(SCHEMA['ENDPOINT_OPER_INFO'])


@app.route('/NetworkDriver.DeleteEndpoint', methods=['POST'])
def network_driver_delete_endpoint():
    return jsonify(SCHEMA['SUCCESS'])


@app.route('/NetworkDriver.Join', methods=['POST'])
def network_driver_join():
    return jsonify(SCHEMA['JOIN'])


@app.route('/NetworkDriver.Leave', methods=['POST'])
def network_driver_leave():
    return jsonify(SCHEMA['SUCCESS'])
