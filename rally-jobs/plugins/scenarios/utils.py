# Copyright 2016: IBM Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import docker

from rally.common import logging
from rally.plugins.openstack import scenario
from rally.task import atomic

LOG = logging.getLogger(__name__)


class KuryrScenario(scenario.OpenStackScenario):
    """Base class for Kuryr scenarios with basic atomic actions."""

    def __init__(self, context=None, admin_clients=None, clients=None):
        super(KuryrScenario, self).__init__(context, admin_clients, clients)
        self.docker_client = docker.Client(base_url='tcp://0.0.0.0:2375')

    @atomic.action_timer("kuryr.list_networks")
    def _list_networks(self, network_list_args):
        """Return user networks list.

        :param network_list_args: network list options
        """
        LOG.debug("Running the list_networks scenario")
        names = network_list_args.get('names')
        ids = network_list_args.get('ids')
        return self.docker_client.networks(names, ids)

    @atomic.action_timer("kuryr.create_network")
    def _create_network(self, network_create_args):
        """Create Kuryr network.

        :param network_create_args: dict: name, driver and others
        :returns: dict of the created network reference object
        """
        name = self.generate_random_name()
        return self.docker_client.create_network(name=name,
                                                 driver='kuryr',
                                                 options=network_create_args
                                                 )

    @atomic.action_timer("kuryr.delete_network")
    def _delete_network(self, network):
        """Delete Kuryr network.

        :param network: Network object
        """
        self.docker_client.remove_network(network['Id'])
