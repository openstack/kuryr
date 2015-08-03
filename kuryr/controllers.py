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

import os

from flask import jsonify
from flask import request
from neutronclient.neutron import client

from kuryr import app
from kuryr.constants import SCHEMA


OS_URL = os.environ.get('OS_URL', 'http://127.0.0.1:9696/')
OS_TOKEN = os.environ.get('OS_TOKEN', '9999888877776666')

# TODO(tfukushima): Retrieve configuration info from a config file.
app.neutron = client.Client('2.0', endpoint_url=OS_URL, token=OS_TOKEN)
app.neutron.format = 'json'


@app.route('/Plugin.Activate', methods=['POST'])
def plugin_activate():
    return jsonify(SCHEMA['PLUGIN_ACTIVATE'])


@app.route('/NetworkDriver.CreateNetwork', methods=['POST'])
def network_driver_create_network():
    """Creates a new Neutron Network which name is the given NetworkID.

    This function takes the following JSON data and delegates the actual
    network creation to the Neutron client. libnetwork's NetworkID is used as
    the name of Network in Neutron. ::

        {
            "NetworkID": string,
            "Options": {
                ...
            }
        }

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#create-network  # noqa
    """
    json_data = request.get_json(force=True)

    app.logger.debug("Received JSON data {0} for /NetworkDriver.CreateNetwork"
                     .format(json_data))
    # TODO(tfukushima): Add a validation of the JSON data for the network.
    neutron_network_name = json_data['NetworkID']

    network = app.neutron.create_network(
        {'network': {'name': neutron_network_name, "admin_state_up": True}})

    app.logger.info("Created a new network with name {0} successfully: {1}"
                    .format(neutron_network_name, network))
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
