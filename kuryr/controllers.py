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

import flask
import jsonschema
import netaddr
from neutronclient.common import exceptions as n_exceptions
from oslo_config import cfg

from kuryr import app
from kuryr.common import constants
from kuryr.common import exceptions
from kuryr import schemata
from kuryr import utils


cfg.CONF.import_group('neutron_client', 'kuryr.common.config')
cfg.CONF.import_group('keystone_client', 'kuryr.common.config')

keystone_conf = cfg.CONF.keystone_client
username = keystone_conf.admin_user
tenant_name = keystone_conf.admin_tenant_name
password = keystone_conf.admin_password
auth_token = keystone_conf.admin_token
auth_uri = keystone_conf.auth_uri.rstrip('/')

neutron_uri = cfg.CONF.neutron_client.neutron_uri

if username and password:
    # Authenticate with password crentials
    app.neutron = utils.get_neutron_client(
        url=neutron_uri, username=username, tenant_name=tenant_name,
        password=password, auth_url=auth_uri)
else:
    app.neutron = utils.get_neutron_client_simple(
        url=neutron_uri, token=auth_token)

# TODO(tfukushima): Retrieve the following subnet names from the config file.
SUBNET_POOLS_V4 = [
    p.strip() for p in os.environ.get('SUBNET_POOLS_V4', 'kuryr').split(',')]
SUBNET_POOLS_V6 = [
    p.strip() for p in os.environ.get('SUBNET_POOLS_V6', 'kuryr6').split(',')]

app.neutron.format = 'json'


def _get_subnets_by_attrs(**attrs):
    subnets = app.neutron.list_subnets(**attrs)
    if len(subnets) > 1:
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron subnets exist for the params {0} "
            .format(', '.join(['{0}={1}'.format(k, v)
                               for k, v in attrs.items()])))
    return subnets['subnets']


def _handle_allocation_from_pools(neutron_network_id, existing_subnets):
    for v4_subnet_name in SUBNET_POOLS_V4:
        v4_subnets = _get_subnets_by_attrs(
            network_id=neutron_network_id, name=v4_subnet_name)
        existing_subnets += v4_subnets

    for v6_subnet_name in SUBNET_POOLS_V6:
        v6_subnets = _get_subnets_by_attrs(
            network_id=neutron_network_id, name=v6_subnet_name)
        existing_subnets += v6_subnets


def _process_subnet(neutron_network_id, endpoint_id, interface_cidr,
                    new_subnets, existing_subnets, pool_id=None):
    cidr = netaddr.IPNetwork(interface_cidr)
    subnet_network = str(cidr.network)
    subnet_cidr = '/'.join([subnet_network,
                            str(cidr.prefixlen)])
    subnets = _get_subnets_by_attrs(
        network_id=neutron_network_id, cidr=subnet_cidr)
    if subnets:
        existing_subnets += subnets
    else:
        new_subnets.append({
            'name': '-'.join([endpoint_id, subnet_network]),
            # Allocate all IP addresses in the subnet.
            'allocation_pools': None,
            'network_id': neutron_network_id,
            'ip_version': cidr.version,
            'cidr': subnet_cidr,
        })


def _handle_explicit_allocation(neutron_network_id, endpoint_id,
                                interface_cidrv4, interface_cidrv6,
                                new_subnets, existing_subnets):
    if interface_cidrv4:
        _process_subnet(neutron_network_id, endpoint_id, interface_cidrv4,
                        new_subnets, existing_subnets)

    if interface_cidrv6:
        _process_subnet(neutron_network_id, endpoint_id, interface_cidrv6,
                        new_subnets, existing_subnets)

    if new_subnets:
        # Bulk create operation of subnets
        created_subnets = app.neutron.create_subnet({'subnets': new_subnets})

        return created_subnets


def _create_subnets_and_or_port(interfaces, neutron_network_id, endpoint_id):
    response_interfaces = []
    for interface in interfaces:
        existing_subnets = []
        created_subnets = {}
        # v4 and v6 Subnets for bulk creation.
        new_subnets = []

        interface_id = interface['ID']
        interface_cidrv4 = interface.get('Address', '')
        interface_cidrv6 = interface.get('AddressIPv6', '')
        interface_mac = interface['MacAddress']

        if interface_cidrv4 or interface_cidrv6:
            created_subnets = _handle_explicit_allocation(
                neutron_network_id, endpoint_id, interface_cidrv4,
                interface_cidrv6, new_subnets, existing_subnets)
        else:
            _handle_allocation_from_pools(
                neutron_network_id, existing_subnets)

        try:
            port = {
                'name': '-'.join([endpoint_id, str(interface_id), 'port']),
                'admin_state_up': True,
                'mac_address': interface_mac,
                'network_id': neutron_network_id,
            }
            created_subnets = created_subnets.get('subnets', [])
            all_subnets = created_subnets + existing_subnets
            fixed_ips = port['fixed_ips'] = []
            for subnet in all_subnets:
                fixed_ip = {'subnet_id': subnet['id']}
                if subnet['ip_version'] == 4:
                    cidr = netaddr.IPNetwork(interface_cidrv4)
                else:
                    cidr = netaddr.IPNetwork(interface_cidrv6)
                subnet_cidr = '/'.join([str(cidr.network),
                                        str(cidr.prefixlen)])
                if subnet['cidr'] != subnet_cidr:
                    continue
                fixed_ip['ip_address'] = str(cidr.ip)
                fixed_ips.append(fixed_ip)
            app.neutron.create_port({'port': port})

            response_interfaces.append({
                'ID': interface_id,
                'Address': interface_cidrv4,
                'AddressIPv6': interface_cidrv6,
                'MacAddress': interface_mac
            })
        except n_exceptions.NeutronClientException as ex:
            app.logger.error("Error happend during creating a "
                             "Neutron port: {0}".format(ex))
            # Rollback the subnets creation
            for subnet in created_subnets:
                app.neutron.delete_subnet(subnet['id'])
            raise

    return response_interfaces


@app.route('/Plugin.Activate', methods=['POST'])
def plugin_activate():
    return flask.jsonify(constants.SCHEMA['PLUGIN_ACTIVATE'])


@app.route('/NetworkDriver.GetCapabilities', methods=['POST'])
def plugin_scope():
    capabilities = {'Scope': cfg.CONF.capability_scope}
    return flask.jsonify(capabilities)


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
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /NetworkDriver.CreateNetwork"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.NETWORK_CREATE_SCHEMA)

    neutron_network_name = json_data['NetworkID']

    network = app.neutron.create_network(
        {'network': {'name': neutron_network_name, "admin_state_up": True}})

    app.logger.info("Created a new network with name {0} successfully: {1}"
                    .format(neutron_network_name, network))
    return flask.jsonify(constants.SCHEMA['SUCCESS'])


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
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /NetworkDriver.DeleteNetwork"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.NETWORK_DELETE_SCHEMA)

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
        return flask.jsonify(constants.SCHEMA['SUCCESS'])


@app.route('/NetworkDriver.CreateEndpoint', methods=['POST'])
def network_driver_create_endpoint():
    """Creates new Neutron Subnets and a Port with the given EndpointID.

    This function takes the following JSON data and delegates the actual
    endpoint creation to the Neutron client mapping it into Subnet and Port. ::

        {
            "NetworkID": string,
            "EndpointID": string,
            "Options": {
                ...
            },
            "Interfaces": [{
                "ID": int,
                "Address": string,
                "AddressIPv6": string,
                "MacAddress": string
            }, ...]
        }

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#create-endpoint  # noqa
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /NetworkDriver.CreateEndpoint"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.ENDPOINT_CREATE_SCHEMA)

    neutron_network_name = json_data['NetworkID']
    endpoint_id = json_data['EndpointID']

    filtered_networks = app.neutron.list_networks(name=neutron_network_name)

    if not filtered_networks:
        return flask.jsonify({
            'Err': "Neutron network associated with ID {0} doesn't exit."
            .format(neutron_network_name)
        })
    elif len(filtered_networks) > 1:
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron Networks exist for NetworkID {0}"
            .format(neutron_network_name))
    else:
        neutron_network_id = filtered_networks['networks'][0]['id']
        interfaces = json_data['Interfaces']
        response_interfaces = _create_subnets_and_or_port(
            interfaces, neutron_network_id, endpoint_id)

        return flask.jsonify({'Interfaces': response_interfaces})


@app.route('/NetworkDriver.EndpointOperInfo', methods=['POST'])
def network_driver_endpoint_operational_info():
    return flask.jsonify(constants.SCHEMA['ENDPOINT_OPER_INFO'])


@app.route('/NetworkDriver.DeleteEndpoint', methods=['POST'])
def network_driver_delete_endpoint():
    """Deletes Neutron Subnets and a Port with the given EndpointID.

    This function takes the following JSON data and delegates the actual
    endpoint deletion to the Neutron client mapping it into Subnet and Port. ::

        {
            "NetworkID": string,
            "EndpointID": string
        }

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#delete-endpoint  # noqa
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /NetworkDriver.DeleteEndpoint"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.ENDPOINT_DELETE_SCHEMA)

    neutron_network_name = json_data['NetworkID']
    endpoint_id = json_data['EndpointID']

    filtered_networks = app.neutron.list_networks(name=neutron_network_name)

    if not filtered_networks:
        return flask.jsonify({
            'Err': "Neutron network associated with ID {0} doesn't exit."
            .format(neutron_network_name)
        })
    elif len(filtered_networks) > 1:
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron Networks exist for NetworkID {0}"
            .format(neutron_network_name))
    else:
        neutron_network_id = filtered_networks['networks'][0]['id']
        filtered_ports = []
        concerned_subnet_ids = []
        try:
            filtered_ports = app.neutron.list_ports(
                network_id=neutron_network_id)
            filtered_ports = [port for port in filtered_ports['ports']
                              if endpoint_id in port['name']]
            for port in filtered_ports:
                fixed_ips = port.get('fixed_ips', [])
                for fixed_ip in fixed_ips:
                    concerned_subnet_ids.append(fixed_ip['subnet_id'])
                app.neutron.delete_port(port['id'])
        except n_exceptions.NeutronClientException as ex:
            app.logger.error("Error happend during deleting a "
                             "Neutron ports: {0}".format(ex))
            raise

        for subnet_id in concerned_subnet_ids:
            # If the subnet to be deleted has any port, when some ports are
            # referring to the subnets in other words, delete_subnet throws an
            # exception, SubnetInUse that extends Conflict. This can happen
            # when the multiple Docker endpoints are created with the same
            # subnet CIDR and it's totally the normal case. So we'd just log
            # that and continue to proceed.
            try:
                app.neutron.delete_subnet(subnet_id)
            except n_exceptions.Conflict as ex:
                app.logger.info("The subnet with ID {0} is still referred "
                                "from other ports and it can't be deleted for "
                                "now.".format(subnet_id))
            except n_exceptions.NeutronClientException as ex:
                app.logger.error("Error happend during deleting a "
                                 "Neutron subnets: {0}".format(ex))
                raise

        return flask.jsonify(constants.SCHEMA['SUCCESS'])


@app.route('/NetworkDriver.Join', methods=['POST'])
def network_driver_join():
    """Binds a Neutron Port to a network interface attached to a container.

    This function takes the following JSON data, creates a veth pair, put one
    end inside of the container and binds another end to the Neutron Port
    specified in the request. ::

        {
            "NetworkID": string,
            "EndpointID": string,
            "SandboxKey": string,
            "Options": {
                ...
            }
        }

    If the binding is succeeded, the following JSON response is returned.::

        {
            "InterfaceName": {
                SrcName: string,
                DstPrefix: string
            },
            "Gateway": string,
            "GatewayIPv6": string,
            "StaticRoutes": [{
                "Destination": string,
                "RouteType": int,
                "NextHop": string,
            }, ...]
        }

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#join  # noqa
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /NetworkDriver.Join"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.JOIN_SCHEMA)

    return flask.jsonify(constants.SCHEMA['JOIN'])


@app.route('/NetworkDriver.Leave', methods=['POST'])
def network_driver_leave():
    return flask.jsonify(constants.SCHEMA['SUCCESS'])
