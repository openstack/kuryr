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

import utils

from rally.plugins.openstack import scenario
from rally.task import validation


class Kuryr(utils.KuryrScenario):
    """Benchmark scenarios for Kuryr."""

    @validation.required_openstack(users=True)
    @scenario.configure(context={"cleanup": ["kuryr"]})
    def list_networks(self, network_list_args=None):
        """List the networks.

        Measure the "docker network ls" command performance under kuryr.

        This will call the docker client API to list networks

        TODO (baohua):
        1. may support tenant/user in future.
        2. validation.required_services add KURYR support

        :param network_list_args: dict: names, ids
        """
        self._list_networks(network_list_args or {})
