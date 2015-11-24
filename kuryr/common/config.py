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

from kuryr import i18n

_ = i18n._

core_opts = [
    cfg.StrOpt('pybasedir',
               default=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    '../../')),
               help=_('Directory where kuryr python module is installed.')),
    cfg.StrOpt('bindir',
               default='$pybasedir/usr/libexec/kuryr',
               help=_('Directory for kuryr vif binding executables.')),
    cfg.StrOpt('kuryr_uri',
               default='http://127.0.0.1:2377',
               help=_('Kuryr URL for accessing Kuryr through json rpc.')),
    cfg.StrOpt('capability_scope',
               default='global',
               choices=['local', 'global'],
               help=_('Kuryr plugin scope reported to libnetwork.')),
]
neutron_opts = [
    cfg.StrOpt('neutron_uri',
               default=os.environ.get('OS_URL', 'http://127.0.0.1:9696'),
               help=_('Neutron URL for accessing the network service.')),
    cfg.StrOpt('enable_dhcp',
               default='False',
               help=_('Enable or Disable dhcp for neutron subnets.')),
]
keystone_opts = [
    cfg.StrOpt('auth_uri',
               default=os.environ.get('IDENTITY_URL',
                                      'http://127.0.0.1:35357'),
               help=_('The URL for accessing the identity service.')),
    cfg.StrOpt('admin_user',
               default=os.environ.get('SERVICE_USER'),
               help=_('The admin username.')),
    cfg.StrOpt('admin_tenant_name',
               default=os.environ.get('SERVICE_TENANT_NAME'),
               help=_('The admin username.')),
    cfg.StrOpt('admin_password',
               default=os.environ.get('SERVICE_PASSWORD'),
               help=_('The admin password.')),
    cfg.StrOpt('admin_token',
               default=os.environ.get('SERVICE_TOKEN'),
               help=_('The admin token.')),
]


CONF = cfg.CONF
CONF.register_opts(core_opts)
CONF.register_opts(neutron_opts, group='neutron_client')
CONF.register_opts(keystone_opts, group='keystone_client')

binding_opts = [
    cfg.StrOpt('veth_dst_prefix',
               default='eth',
               help=('The name prefix of the veth endpoint put inside the '
                     'container.'))
]
CONF.register_opts(binding_opts, 'binding')
