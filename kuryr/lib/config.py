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

import os

from oslo_config import cfg
from oslo_log import log

from kuryr.lib._i18n import _
from kuryr.lib import version


core_opts = [
    cfg.StrOpt('bindir',
               default='$pybasedir/usr/libexec/kuryr',
               help=_('Directory for Kuryr vif binding executables.')),
    cfg.StrOpt('subnetpool_name_prefix',
               default='kuryrPool',
               help=_('Neutron subnetpool name will be prefixed by this.')),
]
neutron_opts = [
    cfg.StrOpt('neutron_uri',
               default=os.environ.get('OS_URL', 'http://127.0.0.1:9696'),
               help=_('Neutron URL for accessing the network service.')),
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
]
keystone_opts = [
    cfg.StrOpt('auth_uri',
               default=os.environ.get('IDENTITY_URL',
                                      'http://127.0.0.1:35357/v2.0'),
               help=_('The URL for accessing the identity service.')),
    cfg.StrOpt('admin_user',
               default=os.environ.get('SERVICE_USER'),
               help=_('The username to auth with the identity service.')),
    cfg.StrOpt('admin_tenant_name',
               default=os.environ.get('SERVICE_TENANT_NAME'),
               help=_('The tenant name to auth with the identity service.')),
    cfg.StrOpt('admin_password',
               default=os.environ.get('SERVICE_PASSWORD'),
               help=_('The password to auth with the identity service.')),
    cfg.StrOpt('admin_token',
               default=os.environ.get('SERVICE_TOKEN'),
               help=_('The admin token.')),
    cfg.StrOpt('auth_ca_cert',
               default=os.environ.get('SERVICE_CA_CERT'),
               help=_('The CA certification file.')),
    cfg.BoolOpt('auth_insecure',
                default=False,
                help=_("Turn off verification of the certificate for ssl")),
]
binding_opts = [
    cfg.StrOpt('veth_dst_prefix',
               default='eth',
               help=('The name prefix of the veth endpoint put inside the '
                     'container.'))
]


CONF = cfg.CONF
CONF.register_opts(core_opts)
CONF.register_opts(neutron_opts, group='neutron_client')
CONF.register_opts(keystone_opts, group='keystone_client')
CONF.register_opts(binding_opts, 'binding')

# Setting oslo.log options for logging.
log.register_options(CONF)


def init(args, **kwargs):
    cfg.CONF(args=args, project='kuryr',
             version=version.version_info.release_string(), **kwargs)
