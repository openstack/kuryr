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
from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_utils import excutils

from kuryr import app
from kuryr import binding
from kuryr.common import config
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


def _cache_default_subnetpool_ids(app):
    """Caches IDs of the default subnetpools as app.DEFAULT_POOL_IDS."""
    if not hasattr(app, 'DEFAULT_POOL_IDS'):
        default_subnetpool_id_set = set()
        try:
            subnetpool_names = SUBNET_POOLS_V4 + SUBNET_POOLS_V6
            for subnetpool_name in subnetpool_names:
                subnetpools = app.neutron.list_subnetpools(
                    name=subnetpool_name)
                for subnetpool in subnetpools['subnetpools']:
                    default_subnetpool_id_set.add(subnetpool['id'])
        except n_exceptions.NeutronClientException as ex:
            app.logger.error("Error happened during retrieving the default "
                             "subnet pools.".format(ex))
        app.DEFAULT_POOL_IDS = frozenset(default_subnetpool_id_set)


def _get_networks_by_attrs(**attrs):
    networks = app.neutron.list_networks(**attrs)
    if len(networks.get('networks', [])) > 1:
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron networks exist for the params {0}"
            .format(', '.join(['{0}={1}'.format(k, v)
                               for k, v in attrs.items()])))
    return networks['networks']


def _get_subnets_by_attrs(**attrs):
    subnets = app.neutron.list_subnets(**attrs)
    if len(subnets.get('subnets', [])) > 2:  # subnets for IPv4 and/or IPv6
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron subnets exist for the params {0} "
            .format(', '.join(['{0}={1}'.format(k, v)
                               for k, v in attrs.items()])))
    return subnets['subnets']


def _get_ports_by_attrs(**attrs):
    ports = app.neutron.list_ports(**attrs)
    if len(ports.get('ports', [])) > 1:
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron ports exist for the params {0} "
            .format(', '.join(['{0}={1}'.format(k, v)
                               for k, v in attrs.items()])))
    return ports['ports']


def _get_subnetpools_by_attrs(**attrs):
    subnetpools = app.neutron.list_subnetpools(**attrs)
    if len(subnetpools.get('subnetpools', [])) > 1:
        raise exceptions.DuplicatedResourceException(
            "Multiple Neutron subnetspool exist for the params {0} "
            .format(', '.join(['{0}={1}'.format(k, v)
                               for k, v in attrs.items()])))
    return subnetpools['subnetpools']


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

        cidr = netaddr.IPNetwork(interface_cidr)
        subnet_network = str(cidr.network)
        subnet_cidr = '/'.join([subnet_network,
                                str(cidr.prefixlen)])
        new_subnet = {
            'name': '-'.join([endpoint_id, subnet_network]),
            'network_id': neutron_network_id,
            'ip_version': cidr.version,
            'cidr': subnet_cidr,
        }
        if pool_id:
            del new_subnet['cidr']
            new_subnet['subnetpool_id'] = pool_id

        new_subnets.append(new_subnet)


def _get_or_create_subnet_by_pools(subnetpool_names, neutron_network_id,
                                   endpoint_id, new_subnets, existing_subnets):
    for subnetpool_name in subnetpool_names:
        pools = _get_subnetpools_by_attrs(name=subnetpool_name)
        if pools:
            pool = pools[0]
            prefixes = pool['prefixes']
            for prefix in prefixes:
                _process_subnet(neutron_network_id, endpoint_id, prefix,
                                new_subnets, existing_subnets,
                                pool_id=pool['id'])
    if not (new_subnets or existing_subnets):
        raise exceptions.NoResourceException(
            "No subnetpools with name {0} is found."
            .format(', '.join(subnetpool_names)))


def _handle_allocation_from_pools(neutron_network_id, endpoint_id,
                                  new_subnets, existing_subnets):
    _get_or_create_subnet_by_pools(SUBNET_POOLS_V4, neutron_network_id,
                                   endpoint_id, new_subnets, existing_subnets)
    _get_or_create_subnet_by_pools(SUBNET_POOLS_V6, neutron_network_id,
                                   endpoint_id, new_subnets, existing_subnets)

    created_subnets_response = {'subnets': []}
    if new_subnets:
        created_subnets_response = app.neutron.create_subnet(
            {'subnets': new_subnets})

    return created_subnets_response


def _handle_explicit_allocation(neutron_network_id, endpoint_id,
                                interface_cidrv4, interface_cidrv6,
                                new_subnets, existing_subnets):
    if interface_cidrv4:
        _process_subnet(neutron_network_id, endpoint_id, interface_cidrv4,
                        new_subnets, existing_subnets)

    if interface_cidrv6:
        _process_subnet(neutron_network_id, endpoint_id, interface_cidrv6,
                        new_subnets, existing_subnets)

    created_subnets_response = {'subnets': []}
    if new_subnets:
        # Bulk create operation of subnets
        created_subnets_response = app.neutron.create_subnet(
            {'subnets': new_subnets})

    return created_subnets_response


def _process_interface_address(port_dict, subnets_dict_by_id,
                               response_interface):
    assigned_address = port_dict['ip_address']
    subnet_id = port_dict['subnet_id']
    subnet = subnets_dict_by_id[subnet_id]
    cidr = netaddr.IPNetwork(subnet['cidr'])
    assigned_address += '/' + str(cidr.prefixlen)
    if cidr.version == 4:
        response_interface['Address'] = assigned_address
    else:
        response_interface['AddressIPv6'] = assigned_address


def _create_subnets_and_or_port(interface, neutron_network_id, endpoint_id):
    response_interface = {}
    existing_subnets = []
    created_subnets_response = {'subnets': []}
    # v4 and v6 Subnets for bulk creation.
    new_subnets = []

    interface_cidrv4 = interface.get('Address', '')
    interface_cidrv6 = interface.get('AddressIPv6', '')
    interface_mac = interface.get('MacAddress', '')

    if interface_cidrv4 or interface_cidrv6:
        created_subnets_response = _handle_explicit_allocation(
            neutron_network_id, endpoint_id, interface_cidrv4,
            interface_cidrv6, new_subnets, existing_subnets)
    else:
        app.logger.info("Retrieving or creating subnets with the default "
                        "subnetpool because Address and AddressIPv6 are "
                        "not given.")
        created_subnets_response = _handle_allocation_from_pools(
            neutron_network_id, endpoint_id, new_subnets, existing_subnets)

    try:
        port = {
            'name': '-'.join([endpoint_id, 'port']),
            'admin_state_up': True,
            'network_id': neutron_network_id,
            'device_owner': constants.DEVICE_OWNER,
            'device_id': endpoint_id,
        }
        if interface_mac:
            port['mac_address'] = interface_mac
        created_subnets = created_subnets_response.get('subnets', [])
        all_subnets = created_subnets + existing_subnets
        fixed_ips = port['fixed_ips'] = []
        for subnet in all_subnets:
            fixed_ip = {'subnet_id': subnet['id']}
            if interface_cidrv4 or interface_cidrv6:
                if subnet['ip_version'] == 4 and interface_cidrv4:
                    cidr = netaddr.IPNetwork(interface_cidrv4)
                elif subnet['ip_version'] == 6 and interface_cidrv6:
                    cidr = netaddr.IPNetwork(interface_cidrv6)
                subnet_cidr = '/'.join([str(cidr.network),
                                        str(cidr.prefixlen)])
                if subnet['cidr'] != subnet_cidr:
                    continue
                fixed_ip['ip_address'] = str(cidr.ip)
            fixed_ips.append(fixed_ip)
        created_port = app.neutron.create_port({'port': port})
        created_port = created_port['port']

        created_fixed_ips = created_port['fixed_ips']
        subnets_dict_by_id = {subnet['id']: subnet
                              for subnet in all_subnets}

        response_interface = {
            'MacAddress': created_port['mac_address']
        }

        if interface_cidrv4 or interface_cidrv6:
            response_interface['Address'] = interface_cidrv4
            response_interface['AddressIPv6'] = interface_cidrv6
        else:
            if 'ip_address' in created_port:
                _process_interface_address(
                    created_port, subnets_dict_by_id, response_interface)
            for fixed_ip in created_fixed_ips:
                _process_interface_address(
                    fixed_ip, subnets_dict_by_id, response_interface)
    except n_exceptions.NeutronClientException as ex:
        app.logger.error("Error happend during creating a "
                         "Neutron port: {0}".format(ex))
        # Rollback the subnets creation
        for subnet in created_subnets:
            app.neutron.delete_subnet(subnet['id'])
        raise

    return response_interface


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

    filtered_networks = _get_networks_by_attrs(name=neutron_network_name)

    # We assume Neutron's Network names are not conflicted in Kuryr because
    # they are Docker IDs, 256 bits hashed values, which are rarely conflicted.
    # However, if there're multiple networks associated with the single
    # NetworkID, it raises DuplicatedResourceException and stops processes.
    # See the following doc for more details about Docker's IDs:
    #   https://github.com/docker/docker/blob/master/docs/terms/container.md#container-ids  # noqa
    neutron_network_id = filtered_networks[0]['id']
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
            "Interface": {
                "Address": string,
                "AddressIPv6": string,
                "MacAddress": string
            }
        }

    Then the following JSON response is returned. ::

        {
            "Interface": {
                "Address": string,
                "AddressIPv6": string,
                "MacAddress": string
            }
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

    filtered_networks = _get_networks_by_attrs(name=neutron_network_name)

    if not filtered_networks:
        return flask.jsonify({
            'Err': "Neutron network associated with ID {0} doesn't exist."
            .format(neutron_network_name)
        })
    else:
        neutron_network_id = filtered_networks[0]['id']
        interface = json_data['Interface'] or {}  # Workaround for null
        response_interface = _create_subnets_and_or_port(
            interface, neutron_network_id, endpoint_id)

        return flask.jsonify({'Interface': response_interface})


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

    filtered_networks = _get_networks_by_attrs(name=neutron_network_name)

    if not filtered_networks:
        return flask.jsonify({
            'Err': "Neutron network associated with ID {0} doesn't exist."
            .format(neutron_network_name)
        })
    else:
        neutron_network_id = filtered_networks[0]['id']
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
            try:
                subnet = app.neutron.show_subnet(subnet_id)
                subnet = subnet['subnet']
                subnetpool_id = subnet.get('subnetpool_id', None)

                _cache_default_subnetpool_ids(app)

                if subnetpool_id not in app.DEFAULT_POOL_IDS:
                    # If the subnet to be deleted has any port, when some ports
                    # are referring to the subnets in other words,
                    # delete_subnet throws an exception, SubnetInUse that
                    # extends Conflict. This can happen when the multiple
                    # Docker endpoints are created with the same subnet CIDR
                    # and it's totally the normal case. So we'd just log that
                    # and continue to proceed.
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

    neutron_network_name = json_data['NetworkID']
    endpoint_id = json_data['EndpointID']

    filtered_networks = _get_networks_by_attrs(name=neutron_network_name)

    if not filtered_networks:
        return flask.jsonify({
            'Err': "Neutron network associated with ID {0} doesn't exit."
            .format(neutron_network_name)
        })
    else:
        neutron_network_id = filtered_networks[0]['id']

        neutron_port_name = utils.get_neutron_port_name(endpoint_id)
        filtered_ports = _get_ports_by_attrs(name=neutron_port_name)
        if not filtered_ports:
            raise exceptions.NoResourceException(
                "The port doesn't exist for the name {0}"
                .format(neutron_port_name))
        neutron_port = filtered_ports[0]
        all_subnets = _get_subnets_by_attrs(network_id=neutron_network_id)

        try:
            ifname, peer_name, (stdout, stderr) = binding.port_bind(
                endpoint_id, neutron_port, all_subnets)
            app.logger.debug(stdout)
            if stderr:
                app.logger.error(stderr)
        except exceptions.VethCreationFailure as ex:
            with excutils.save_and_reraise_exception():
                app.logger.error('Preparing the veth pair was failed: {0}.'
                                 .format(ex))
        except processutils.ProcessExecutionError:
            with excutils.save_and_reraise_exception():
                app.logger.error(
                    'Could not bind the Neutron port to the veth endpoint.')

        join_response = {
            "InterfaceName": {
                "SrcName": peer_name,
                "DstPrefix": config.CONF.binding.veth_dst_prefix
            },
            "StaticRoutes": []
        }

        for subnet in all_subnets:
            if subnet['ip_version'] == 4:
                join_response['Gateway'] = subnet.get('gateway_ip', '')
            else:
                join_response['GatewayIPv6'] = subnet.get('gateway_ip', '')
            host_routes = subnet.get('host_routes', [])

            for host_route in host_routes:
                static_route = {
                    'Destination': host_route['destination']
                }
                if host_route.get('nexthop', None):
                    static_route['RouteType'] = constants.TYPES['NEXTHOP']
                    static_route['NextHop'] = host_route['nexthop']
                else:
                    static_route['RouteType'] = constants.TYPES['CONNECTED']
                join_response['StaticRoutes'].append(static_route)

        return flask.jsonify(join_response)


@app.route('/NetworkDriver.Leave', methods=['POST'])
def network_driver_leave():
    """Unbinds a Neutron Port to a network interface attached to a container.

    This function takes the following JSON data and delete the veth pair
    corresponding to the given info. ::

        {
            "NetworkID": string,
            "EndpointID": string
        }
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /NetworkDriver.DeleteEndpoint"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.LEAVE_SCHEMA)
    neutron_network_name = json_data['NetworkID']
    endpoint_id = json_data['EndpointID']

    filtered_networks = _get_networks_by_attrs(name=neutron_network_name)

    if not filtered_networks:
        return flask.jsonify({
            'Err': "Neutron network associated with ID {0} doesn't exit."
            .format(neutron_network_name)
        })
    else:
        neutron_port_name = '-'.join([endpoint_id, 'port'])
        filtered_ports = _get_ports_by_attrs(name=neutron_port_name)
        if not filtered_ports:
            raise exceptions.NoResourceException(
                "The port doesn't exist for the name {0}"
                .format(neutron_port_name))
        neutron_port = filtered_ports[0]
        try:
            stdout, stderr = binding.port_unbind(endpoint_id, neutron_port)
            app.logger.debug(stdout)
            if stderr:
                app.logger.error(stderr)
        except processutils.ProcessExecutionError:
            with excutils.save_and_reraise_exception():
                app.logger.error(
                    'Could not unbind the Neutron port from the veth '
                    'endpoint.')
        except exceptions.VethDeletionFailure:
            with excutils.save_and_reraise_exception():
                app.logger.error('Cleaning the veth pair up was failed.')

    return flask.jsonify(constants.SCHEMA['SUCCESS'])
