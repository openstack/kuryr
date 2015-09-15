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

from kuryr import app
from kuryr.constants import SCHEMA
from kuryr import exceptions
from kuryr import utils


# TODO(tfukushima): Retrieve configuration info from a config file.
OS_URL = os.environ.get('OS_URL', 'http://127.0.0.1:9696/')
OS_TOKEN = os.environ.get('OS_TOKEN', '9999888877776666')
OS_AUTH_URL = os.environ.get('OS_AUTH_URL', 'https://127.0.0.1:5000/v2.0/')
OS_USERNAME = os.environ.get('OS_USERNAME', '')
OS_PASSWORD = os.environ.get('OS_PASSWORD', '')
OS_TENANT_NAME = os.environ.get('OS_TENANT_NAME', '')

if OS_USERNAME and OS_PASSWORD:
    # Authenticate with password crentials
    app.neutron = utils.get_neutron_client(
        url=OS_URL, username=OS_USERNAME, tenant_name=OS_TENANT_NAME,
        password=OS_PASSWORD, auth_url=OS_AUTH_URL)
else:
    app.neutron = utils.get_neutron_client_simple(url=OS_URL, token=OS_TOKEN)

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
    """Deletes the Neutron Network which name is the given NetworkID.

    This function takes the following JSON data and delegates the actual
    network deletion to the Neutron client. ::

        {
            "NetworkID": string
        }

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#delete-network  # noqa
    """
    json_data = request.get_json(force=True)

    app.logger.debug("Received JSON data {0} for /NetworkDriver.DeleteNetwork"
                     .format(json_data))
    # TODO(tfukushima): Add a validation of the JSON data for the network.
    neutron_network_name = json_data['NetworkID']

    filtered_networks = app.neutron.list_networks(name=neutron_network_name)

    # We assume Neutron's Network names are not conflicted in Kuryr because
    # they are Docker IDs, 256 bits hashed values, which are rarely conflicted.
    # However, if there're multiple networks associated with the single
    # NetworkID, it raises DuplicatedResourceException and stops processes.
    # See the following doc for more details about Docker's IDs:
    #   https://github.com/docker/docker/blob/master/docs/terms/container.md#container-ids  # noqa
    if len(filtered_networks) > 1:
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron Networks exist for NetworkID {0}"
            .format(neutron_network_name))
    else:
        neutron_network_id = filtered_networks['networks'][0]['id']
        app.neutron.delete_network(neutron_network_id)
        app.logger.info("Deleted the network with ID {0} successfully"
                        .format(neutron_network_id))
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
