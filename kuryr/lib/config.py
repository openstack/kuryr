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

"""
Routines for configuring Kuryr
"""

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg

from kuryr.lib._i18n import _


core_opts = [
    cfg.StrOpt('bindir',
               default='/usr/libexec/kuryr',
               help=_('Directory for Kuryr vif binding executables.')),
    cfg.StrOpt('subnetpool_name_prefix',
               default='kuryrPool',
               help=_('Neutron subnetpool name will be prefixed by this.')),
    cfg.StrOpt('deployment_type',
               default='baremetal',
               help=_("baremetal or nested-containers are the supported"
                      " values.")),
]

neutron_group = cfg.OptGroup(
    'neutron',
    title='Neutron Options',
    help=_('Configuration options for OpenStack Neutron'))

neutron_opts = [
    cfg.StrOpt('enable_dhcp',
               default='True',
               help=_('Enable or Disable dhcp for neutron subnets.')),
    cfg.StrOpt('default_subnetpool_v4',
               default='kuryr',
               help=_('Name of default subnetpool version 4')),
    cfg.StrOpt('default_subnetpool_v6',
               default='kuryr6',
               help=_('Name of default subnetpool version 6')),
    cfg.BoolOpt('vif_plugging_is_fatal',
                default=False,
                help=_("Whether a plugging operation is failed if the port "
                       "to plug does not become active")),
    cfg.IntOpt('vif_plugging_timeout',
               default=0,
               help=_("Seconds to wait for port to become active")),
    cfg.StrOpt('endpoint_type',
               default='public',
               choices=['public', 'admin', 'internal'],
               help=_('Type of the neutron endpoint to use. This endpoint '
                      'will be looked up in the keystone catalog and should '
                      'be one of public, internal or admin.')),
]

binding_opts = [
    cfg.StrOpt('veth_dst_prefix',
               default='eth',
               help=_('The name prefix of the veth endpoint put inside the '
                     'container.')),
    cfg.StrOpt('driver',
               default='kuryr.lib.binding.drivers.veth',
               help=_('Driver to use for binding and unbinding ports.')),
    cfg.StrOpt('link_iface',
               default='',
               help=_('Specifies the name of the Nova instance interface to '
                      'link the virtual devices to (only applicable to some '
                      'binding drivers.')),
]

binding_group = cfg.OptGroup(
    'binding',
    title='binding options',
    help=_('Configuration options for container interface binding.'))


def register_keystoneauth_opts(conf, conf_group):
    ks_loading.register_session_conf_options(conf, conf_group)
    ks_loading.register_auth_conf_options(conf, conf_group)


def register_neutron_opts(conf):
    conf.register_group(neutron_group)
    conf.register_opts(neutron_opts, group=neutron_group)
    register_keystoneauth_opts(conf, neutron_group.name)
