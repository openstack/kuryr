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

__all__ = [
    'list_kuryr_opts',
]

import copy
import itertools
import operator

from keystoneauth1 import loading as ks_loading
from oslo_log import _options

from kuryr.lib import config


ENABLED_AUTH_PLUGINS = ('password', 'v2password', 'v2token', 'v3password',
                        'v3token')

_core_opts_with_logging = config.core_opts
_core_opts_with_logging += _options.common_cli_opts
_core_opts_with_logging += _options.logging_cli_opts
_core_opts_with_logging += _options.generic_log_opts

_kuryr_opts = [
    (None, list(itertools.chain(_core_opts_with_logging))),
]


def get_keystoneauth_conf_options():
    opt_list = []
    opt_list.insert(0, ks_loading.get_auth_common_conf_options()[0])
    opt_list += ks_loading.get_session_conf_options()
    # NOTE(apuimedo): There are a lot of auth plugins, we just generate the
    # config options for a few common ones
    for name in ENABLED_AUTH_PLUGINS:
        for plugin_option in ks_loading.get_auth_plugin_conf_options(name):
            if all(option.name != plugin_option.name for option in opt_list):
                opt_list.append(plugin_option)
    return opt_list


def list_neutron_opts():
    opt_list = copy.deepcopy(config.neutron_opts)
    opt_list += get_keystoneauth_conf_options()
    opt_list.sort(key=operator.attrgetter('name'))
    return [(config.neutron_group, opt_list)]


def list_kuryr_opts():
    """Return a list of oslo_config options available in Kuryr service.

    Each element of the list is a tuple. The first element is the name of the
    group under which the list of elements in the second element will be
    registered. A group name of None corresponds to the [DEFAULT] group in
    config files.

    This function is also discoverable via the 'kuryr' entry point under
    the 'oslo_config.opts' namespace.

    The purpose of this is to allow tools like the Oslo sample config file
    generator to discover the options exposed to users by Kuryr.

    :returns: a list of (group_name, opts) tuples
    """

    return ([(k, copy.deepcopy(o)) for k, o in _kuryr_opts] +
            list_neutron_opts() +
            [(config.binding_group, config.binding_opts)])
