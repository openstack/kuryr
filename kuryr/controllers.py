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
import os_client_config

import flask
import jsonschema
import netaddr

from neutronclient.common import exceptions as n_exceptions
from neutronclient.neutron import client
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


MANDATORY_NEUTRON_EXTENSION = "subnet_allocation"


def _get_cloud_config(cloud='devstack-admin'):
    return os_client_config.OpenStackConfig().get_one_cloud(cloud=cloud)


def _credentials(cloud='devstack-admin'):
    """Retrieves credentials to run functional tests

    Credentials are either read via os-client-config from the environment
    or from a config file ('clouds.yaml'). Environment variables override
    those from the config file.

    devstack produces a clouds.yaml with two named clouds - one named
    'devstack' which has user privs and one named 'devstack-admin' which
    has admin privs. This function will default to getting the devstack-admin
    cloud as that is the current expected behavior.
    """
    return _get_cloud_config(cloud=cloud).get_auth_args()


def _get_neutron_client_from_creds():
    creds = _credentials()
    username = creds['username']
    tenant_name = creds['project_name']
    password = creds['password']
    auth_url = creds['auth_url'] + "/v2.0"
    neutron_client = client.Client('2.0', username=username,
                                   tenant_name=tenant_name,
                                   password=password,
                                   auth_url=auth_url)
    return neutron_client


def get_neutron_client():
    """Creates the Neutron client for communicating with Neutron."""
    try:
        # First try to retrieve neutron client from a working OS deployment
        # This is used for gate testing.
        # Since this always use admin credentials, next patch will introduce
        # a config parameter that disable this for production environments
        neutron_client = _get_neutron_client_from_creds()
        return neutron_client
    except Exception:
            pass
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
        neutron_client = utils.get_neutron_client(
            url=neutron_uri, username=username, tenant_name=tenant_name,
            password=password, auth_url=auth_uri)
    else:
        neutron_client = utils.get_neutron_client_simple(
            url=neutron_uri, auth_url=auth_uri, token=auth_token)
    return neutron_client


def neutron_client():
    if not hasattr(app, 'neutron'):
        app.neutron = get_neutron_client()
        app.enable_dhcp = cfg.CONF.neutron_client.enable_dhcp
        app.neutron.format = 'json'


def check_for_neutron_ext_support():
    """Validates for mandatory extension support availability in neutron."""
    try:
        app.neutron.show_extension(MANDATORY_NEUTRON_EXTENSION)
    except n_exceptions.NeutronClientException as e:
        if e.status_code == n_exceptions.NotFound.status_code:
            raise exceptions.MandatoryApiMissing(
                            "Neutron extension with alias '{0}' not found"
                            .format(MANDATORY_NEUTRON_EXTENSION))


# TODO(tfukushima): Retrieve the following subnet names from the config file.
SUBNET_POOLS_V4 = [
    p.strip() for p in os.environ.get('SUBNET_POOLS_V4', 'kuryr').split(',')]
SUBNET_POOLS_V6 = [
    p.strip() for p in os.environ.get('SUBNET_POOLS_V6', 'kuryr6').split(',')]


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


def _get_subnet_cidr_using_cidr(cidr):
    subnet_network = str(cidr.network)
    subnet_cidr = '/'.join([subnet_network,
                            str(cidr.prefixlen)])
    return subnet_cidr


def _get_subnets_by_interface_cidr(neutron_network_id,
                                   interface_cidr):
    cidr = netaddr.IPNetwork(interface_cidr)
    subnet_network = cidr.network
    subnet_cidr = '/'.join([str(subnet_network),
                            str(cidr.prefixlen)])
    subnets = _get_subnets_by_attrs(
        network_id=neutron_network_id, cidr=subnet_cidr)
    return subnets


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


def _create_port(endpoint_id, neutron_network_id, interface_mac, fixed_ips):
    port = {
        'name': utils.get_neutron_port_name(endpoint_id),
        'admin_state_up': True,
        'network_id': neutron_network_id,
        'device_owner': constants.DEVICE_OWNER,
        'device_id': endpoint_id,
        'binding:host_id': utils.get_hostname(),
        'fixed_ips': fixed_ips
    }
    if interface_mac:
        port['mac_address'] = interface_mac
    try:
        rcvd_port = app.neutron.create_port({'port': port})
    except n_exceptions.NeutronClientException as ex:
        app.logger.error("Error happend during creating a "
                         "Neutron port: {0}".format(ex))
        raise
    return rcvd_port['port']


def _update_port(port, endpoint_id):
    port['name'] = utils.get_neutron_port_name(endpoint_id)
    try:
        response_port = app.neutron.update_port(
                port['id'], {'port': {'name': port['name']}})
    except n_exceptions.NeutronClientException as ex:
        app.logger.error("Error happend during creating a "
                         "Neutron port: {0}".format(ex))
        raise
    return response_port['port']


def _get_fixed_ips_by_interface_cidr(subnets, interface_cidrv4,
                                     interface_cidrv6, fixed_ips):
    for subnet in subnets:
        fixed_ip = [('subnet_id=%s' % subnet['id'])]
        if interface_cidrv4 or interface_cidrv6:
            if subnet['ip_version'] == 4 and interface_cidrv4:
                cidr = netaddr.IPNetwork(interface_cidrv4)
            elif subnet['ip_version'] == 6 and interface_cidrv6:
                cidr = netaddr.IPNetwork(interface_cidrv6)
            subnet_cidr = '/'.join([str(cidr.network),
                                   str(cidr.prefixlen)])
            if subnet['cidr'] != subnet_cidr:
                continue
            fixed_ip.append('ip_address=%s' % str(cidr.ip))
        fixed_ips.extend(fixed_ip)


def _create_or_update_port(neutron_network_id, endpoint_id,
        interface_cidrv4, interface_cidrv6, interface_mac):
    response_interface = {}
    subnets = []
    fixed_ips = []

    subnetsv4 = subnetsv6 = []
    if interface_cidrv4:
        subnetsv4 = _get_subnets_by_interface_cidr(
            neutron_network_id, interface_cidrv4)
    if interface_cidrv6:
        subnetsv6 = _get_subnets_by_interface_cidr(
            neutron_network_id, interface_cidrv6)
    subnets = subnetsv4 + subnetsv6
    if not len(subnets):
        raise exceptions.NoResourceException(
            "No subnet exist for the cidrs {0} and {1} "
            .format(interface_cidrv4, interface_cidrv6))
    if len(subnets) > 2:
        raise exceptions.DuplicatedResourceException(
            "Multiple subnets exist for the cidrs {0} and {1}"
            .format(interface_cidrv4, interface_cidrv6))

    _get_fixed_ips_by_interface_cidr(subnets, interface_cidrv4,
        interface_cidrv6, fixed_ips)
    filtered_ports = app.neutron.list_ports(fixed_ips=fixed_ips)
    num_port = len(filtered_ports.get('ports', []))
    if not num_port:
        fixed_ips = utils.get_dict_format_fixed_ips_from_kv_format(fixed_ips)
        response_port = _create_port(endpoint_id, neutron_network_id,
            interface_mac, fixed_ips)
    elif num_port == 1:
        port = filtered_ports['ports'][0]
        response_port = _update_port(port, endpoint_id)
    else:
        raise n_exceptions.DuplicatedResourceException(
            "Multiple ports exist for the cidrs {0} and {1}"
            .format(interface_cidrv4, interface_cidrv6))

    created_fixed_ips = response_port['fixed_ips']
    subnets_dict_by_id = {subnet['id']: subnet
                          for subnet in subnets}
    if not interface_mac:
        response_interface['MacAddress'] = response_port['mac_address']

    if not (interface_cidrv4 or interface_cidrv6):
        if 'ip_address' in response_port:
            _process_interface_address(
                response_port, subnets_dict_by_id, response_interface)
        for fixed_ip in created_fixed_ips:
            _process_interface_address(
                fixed_ip, subnets_dict_by_id, response_interface)

    return response_interface


@app.route('/Plugin.Activate', methods=['POST'])
def plugin_activate():
    """Returns the list of the implemented drivers.

    This function returns the list of the implemented drivers defaults to
    ``[NetworkDriver, IpamDriver]`` in the handshake of the remote driver,
     which happens right before the first request against Kuryr.

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#handshake  # noqa
    """
    return flask.jsonify(constants.SCHEMA['PLUGIN_ACTIVATE'])


@app.route('/NetworkDriver.GetCapabilities', methods=['POST'])
def plugin_scope():
    """Returns the capability as the remote network driver.

    This function returns the capability of the remote network driver, which is
    ``global`` or ``local`` and defaults to ``global``. With ``global``
    capability, the network information is shared among multipe Docker daemons
    if the distributed store is appropriately configured.

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#set-capability  # noqa
    """
    capabilities = {'Scope': cfg.CONF.capability_scope}
    return flask.jsonify(capabilities)


@app.route('/NetworkDriver.DiscoverNew', methods=['POST'])
def network_driver_discover_new():
    """The callback function for the DiscoverNew notification.

    The DiscoverNew notification includes the type of the
    resource that has been newly discovered and possibly other
    information associated with the resource.

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#discovernew-notification  # noqa
    """
    return flask.jsonify(constants.SCHEMA['SUCCESS'])


@app.route('/NetworkDriver.DiscoverDelete', methods=['POST'])
def network_driver_discover_delete():
    """The callback function for the DiscoverDelete notification.

    The DiscoverDelete notification includes the type of the
    resource that has been deleted and possibly other
    information associated with the resource.

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/remote.md#discoverdelete-notification  # noqa
    """
    return flask.jsonify(constants.SCHEMA['SUCCESS'])


@app.route('/NetworkDriver.CreateNetwork', methods=['POST'])
def network_driver_create_network():
    """Creates a new Neutron Network which name is the given NetworkID.

    This function takes the following JSON data and delegates the actual
    network creation to the Neutron client. libnetwork's NetworkID is used as
    the name of Network in Neutron. ::

        {
            "NetworkID": string,
            "IPv4Data" : [{
                "AddressSpace": string,
                "Pool": ipv4-cidr-string,
                "Gateway" : ipv4-address,
                "AuxAddresses": {
                    "<identifier1>" : "<ipv4-address1>",
                    "<identifier2>" : "<ipv4-address2>",
                    ...
                }
            }, ...],
            "IPv6Data" : [{
                "AddressSpace": string,
                "Pool": ipv6-cidr-string,
                "Gateway" : ipv6-address,
                "AuxAddresses": {
                    "<identifier1>" : "<ipv6-address1>",
                    "<identifier2>" : "<ipv6-address2>",
                    ...
                }
            }, ...],
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
    pool_cidr = json_data['IPv4Data'][0]['Pool']
    network = app.neutron.create_network(
        {'network': {'name': neutron_network_name, "admin_state_up": True}})

    app.logger.info("Created a new network with name {0} successfully: {1}"
                    .format(neutron_network_name, network))

    cidr = netaddr.IPNetwork(pool_cidr)
    subnet_network = str(cidr.network)
    subnet_cidr = '/'.join([subnet_network, str(cidr.prefixlen)])
    subnets = _get_subnets_by_attrs(
        network_id=network['network']['id'], cidr=subnet_cidr)
    if not subnets:
        new_subnets = [{
            'name': pool_cidr,
            'network_id': network['network']['id'],
            'ip_version': cidr.version,
            'cidr': subnet_cidr,
            'enable_dhcp': app.enable_dhcp,
        }]
        app.neutron.create_subnet({'subnets': new_subnets})

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
    try:
        filtered_networks = _get_networks_by_attrs(name=neutron_network_name)
    except n_exceptions.NeutronClientException as ex:
        app.logger.error("Error happened during listing "
                         "Neutron networks: {0}".format(ex))
        raise
    # We assume Neutron's Network names are not conflicted in Kuryr because
    # they are Docker IDs, 256 bits hashed values, which are rarely conflicted.
    # However, if there're multiple networks associated with the single
    # NetworkID, it raises DuplicatedResourceException and stops processes.
    # See the following doc for more details about Docker's IDs:
    #   https://github.com/docker/docker/blob/master/docs/terms/container.md#container-ids  # noqa
    neutron_network_id = filtered_networks[0]['id']
    filtered_subnets = _get_subnets_by_attrs(
        network_id=neutron_network_id)
    for subnet in filtered_subnets:
        try:
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
                app.neutron.delete_subnet(subnet['id'])
        except n_exceptions.Conflict as ex:
            app.logger.error("Subnet, {0}, is in use. "
                             "Network cant be deleted.".format(subnet['id']))
            raise
        except n_exceptions.NeutronClientException as ex:
            app.logger.error("Error happened during deleting a "
                             "Neutron subnets: {0}".format(ex))
            raise

    try:
        app.neutron.delete_network(neutron_network_id)
    except n_exceptions.NeutronClientException as ex:
        app.logger.error("Error happened during deleting a "
                         "Neutron network: {0}".format(ex))
        raise
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
        interface_cidrv4 = interface.get('Address', '')
        interface_cidrv6 = interface.get('AddressIPv6', '')
        interface_mac = interface.get('MacAddress', '')
        if not interface_cidrv4 and not interface_cidrv6:
            return flask.jsonify({
                'Err': "Interface address v4 or v6 not provided."
            })
        response_interface = _create_or_update_port(
            neutron_network_id, endpoint_id, interface_cidrv4,
            interface_cidrv6, interface_mac)

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
        neutron_port_name = utils.get_neutron_port_name(endpoint_id)
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


@app.route('/IpamDriver.GetDefaultAddressSpaces', methods=['POST'])
def ipam_get_default_address_spaces():
    """Provides the default address spaces for the IPAM.

    This function is called after the registration of the IPAM driver and
    the plugin set the returned values as the default address spaces for the
    IPAM. The address spaces can be configured in the config file.

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/ipam.md#getdefaultaddressspaces  # noqa
    """
    app.logger.debug("Received /IpamDriver.GetDefaultAddressSpaces")
    address_spaces = {
        'LocalDefaultAddressSpace': cfg.CONF.local_default_address_space,
        'GlobalDefaultAddressSpace': cfg.CONF.global_default_address_space}
    return flask.jsonify(address_spaces)


@app.route('/IpamDriver.RequestPool', methods=['POST'])
def ipam_request_pool():
    """Creates a new Neutron subnetpool from the given request.

    This funciton takes the following JSON data and delegates the subnetpool
    creation to the Neutron client. ::

        {
            "AddressSpace": string
            "Pool":         string
            "SubPool":      string
            "Options":      map[string]string
            "V6":           bool
        }

    Then the following JSON response is returned. ::

        {
            "PoolID": string
            "Pool":   string
            "Data":   map[string]string
        }

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/ipam.md#requestpool  # noqa
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /IpamDriver.RequestPool"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.REQUEST_POOL_SCHEMA)
    requested_pool = json_data['Pool']
    requested_subpool = json_data['SubPool']
    v6 = json_data['V6']
    pool_id = ''
    subnet_cidr = ''
    if requested_pool:
        app.logger.info("Creating subnetpool with the given pool CIDR")
        if requested_subpool:
            cidr = netaddr.IPNetwork(requested_subpool)
        else:
            cidr = netaddr.IPNetwork(requested_pool)
        subnet_cidr = _get_subnet_cidr_using_cidr(cidr)
        pool_name = utils.get_neutron_subnetpool_name(subnet_cidr)
        # Check if requested pool already exist
        pools = _get_subnetpools_by_attrs(name=pool_name)
        if pools:
            pool_id = pools[0]['id']
        if not pools:
            new_subnetpool = {
                'name': pool_name,
                'default_prefixlen': cidr.prefixlen,
                'prefixes': [subnet_cidr]}
            created_subnetpool_response = app.neutron.create_subnetpool(
                {'subnetpool': new_subnetpool})
            pool = created_subnetpool_response['subnetpool']
            pool_id = pool['id']
    else:
        if v6:
            default_pool_list = SUBNET_POOLS_V6
        else:
            default_pool_list = SUBNET_POOLS_V4
        pool_name = default_pool_list[0]
        pools = _get_subnetpools_by_attrs(name=pool_name)
        if pools:
            pool = pools[0]
            pool_id = pool['id']
            prefixes = pool['prefixes']
            if len(prefixes) > 1:
                app.logger.warning("More than one prefixes present. "
                                   "Picking first one.")
            cidr = netaddr.IPNetwork(prefixes[0])
            subnet_cidr = _get_subnet_cidr_using_cidr(cidr)
        else:
            app.logger.error("Default neutron pools not found")
    req_pool_res = {'PoolID': pool_id,
                    'Pool': subnet_cidr}
    return flask.jsonify(req_pool_res)


@app.route('/IpamDriver.RequestAddress', methods=['POST'])
def ipam_request_address():
    """Allocates the IP address in the given request.

    This function takes the following JSON data and add the given IP address in
    the allocation_pools attribute of the subnet. ::

        {
            "PoolID":  string
            "Address": string
            "Options": map[string]string
        }

    Then the following response is returned. ::

        {
            "Address": string
            "Data":    map[string]string
        }

    See the following link for more details about the spec:

    https://github.com/docker/libnetwork/blob/master/docs/ipam.md#requestaddress  # noqa
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /IpamDriver.RequestAddress"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.REQUEST_ADDRESS_SCHEMA)
    pool_id = json_data['PoolID']
    req_address = json_data['Address']
    allocated_address = ''
    subnet_cidr = ''
    pool_prefix_len = ''
    pools = _get_subnetpools_by_attrs(id=pool_id)
    if pools:
        pool = pools[0]
        prefixes = pool['prefixes']
        if len(prefixes) > 1:
            app.logger.warning("More than one prefixes present. Picking "
                               "first one.")

        for prefix in prefixes:
            cidr = netaddr.IPNetwork(prefix)
            pool_prefix_len = str(cidr.prefixlen)
            subnet_network = str(cidr.network)
            subnet_cidr = '/'.join([subnet_network, pool_prefix_len])
            break
    else:
        raise exceptions.NoResourceException(
            "No subnetpools with id {0} is found."
            .format(pool_id))
    # check if any subnet with matching cidr is present
    subnets = _get_subnets_by_attrs(cidr=subnet_cidr)
    if subnets:
        subnet = subnets[0]
        # allocating address for container port
        neutron_network_id = subnet['network_id']
        try:
            port = {
                'name': 'kuryr-unbound-port',
                'admin_state_up': True,
                'network_id': neutron_network_id,
                'binding:host_id': utils.get_hostname(),
            }
            fixed_ips = port['fixed_ips'] = []
            fixed_ip = {'subnet_id': subnet['id']}
            if req_address:
                fixed_ip['ip_address'] = req_address
            fixed_ips.append(fixed_ip)
            created_port_resp = app.neutron.create_port({'port': port})
            created_port = created_port_resp['port']
            allocated_address = created_port['fixed_ips'][0]['ip_address']
            allocated_address = '/'.join(
                [allocated_address, str(cidr.prefixlen)])
        except n_exceptions.NeutronClientException as ex:
            app.logger.error("Error happend during ip allocation on"
                             "Neutron side: {0}".format(ex))
            raise
    else:
        # Auxiliary address or gw_address is received at network creation time.
        # This address cannot be reserved with neutron at this time as subnet
        # is not created yet. In /NetworkDriver.CreateNetwork this address will
        # be reserved with neutron.
        if req_address:
            allocated_address = '/'.join([req_address, pool_prefix_len])

    return flask.jsonify({'Address': allocated_address})


@app.route('/IpamDriver.ReleasePool', methods=['POST'])
def ipam_release_pool():
    """Deletes a new Neutron subnetpool from the given reuest.

    This function takes the following JSON data and delegates the subnetpool
    deletion to the Neutron client. ::

       {
           "PoolID": string
       }

    Then the following JSON response is returned. ::

       {}

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/ipam.md#releasepool  # noqa
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /IpamDriver.ReleasePool"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.RELEASE_POOL_SCHEMA)
    pool_id = json_data['PoolID']
    try:
        app.neutron.delete_subnetpool(pool_id)
    except n_exceptions.Conflict as ex:
        app.logger.info("The subnetpool with ID {0} is still in use."
                        " It can't be deleted for now.".format(pool_id))
    except n_exceptions.NeutronClientException as ex:
        app.logger.error("Error happend during deleting a "
                         "Neutron subnetpool: {0}".format(ex))
        raise

    return flask.jsonify(constants.SCHEMA['SUCCESS'])


@app.route('/IpamDriver.ReleaseAddress', methods=['POST'])
def ipam_release_address():
    """Deallocates the IP address in the given request.

    This function takes the following JSON data and remove the given IP address
    from the allocation_pool attribute of the subnet. ::

        {
            "PoolID": string
            "Address": string
        }

    Then the following response is returned. ::

        {}

    See the following link for more details about the spec:

      https://github.com/docker/libnetwork/blob/master/docs/ipam.md#releaseaddress  # noqa
    """
    json_data = flask.request.get_json(force=True)
    app.logger.debug("Received JSON data {0} for /IpamDriver.ReleaseAddress"
                     .format(json_data))
    jsonschema.validate(json_data, schemata.RELEASE_ADDRESS_SCHEMA)
    pool_id = json_data['PoolID']
    rel_address = json_data['Address']
    filtered_ports = []
    pools = _get_subnetpools_by_attrs(id=pool_id)
    if pools:
        pool = pools[0]
        prefixes = pool['prefixes']
        for prefix in prefixes:
            cidr = netaddr.IPNetwork(prefix)
            subnet_network = str(cidr.network)
            subnet_cidr = '/'.join([subnet_network, str(cidr.prefixlen)])
    else:
        raise exceptions.NoResourceException(
            "No subnetpools with id {0} is found."
            .format(pool_id))
    # check if any subnet with matching cidr is present
    subnets = _get_subnets_by_attrs(cidr=subnet_cidr)
    if not len(subnets):
        raise exceptions.NoResourceException(
            "No subnet is found using pool {0} "
            "and pool_cidr {1}".format(pool_id, cidr))
    subnet = subnets[0]
    cidr_address = netaddr.IPNetwork(rel_address)
    rcvd_fixed_ips = []
    fixed_ip = {'subnet_id': subnet['id']}
    fixed_ip['ip_address'] = str(cidr_address.ip)
    rcvd_fixed_ips.append(fixed_ip)

    try:
        filtered_ports = []
        all_ports = app.neutron.list_ports()
        for port in all_ports['ports']:
            if port['fixed_ips'] == rcvd_fixed_ips:
                filtered_ports.append(port)
        for port in filtered_ports:
            app.neutron.delete_port(port['id'])
    except n_exceptions.NeutronClientException as ex:
        app.logger.error("Error happend while fetching and deleting port, "
                         "{0}".format(ex))
        raise

    return flask.jsonify(constants.SCHEMA['SUCCESS'])

neutron_client()
