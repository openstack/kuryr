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
from oslo_config import cfg
from oslo_utils import importutils

from kuryr.lib import exceptions


def _verify_driver(driver):
    if driver.__name__ not in cfg.CONF.binding.enabled_drivers:
        raise exceptions.DriverNotEnabledException(
            'Driver %s is not enabled' % driver.__name__)


def port_bind(endpoint_id, port, subnets, network=None, vm_port=None,
              segmentation_id=None, driver=None, **kwargs):
    """Binds the Neutron port to the network interface on the host.

    :param endpoint_id:   the ID of the endpoint as string
    :param port:         the container Neutron port dictionary as returned by
                         python-neutronclient
    :param subnets:      an iterable of all the Neutron subnets which the
                         endpoint is trying to join
    :param network:      the Neutron network which the endpoint is trying to
                         join
    :param vm_port:      the Nova instance port dictionary, as returned by
                         python-neutronclient. Binding is being done for the
                         port of a container which is running inside this Nova
                         instance (either ipvlan/macvlan or a subport).
    :param segmentation_id: ID of the segment for container traffic isolation)
    :param driver:       the binding driver name
    :param kwargs:       Additional driver-specific arguments
    :returns: the tuple of the names of the veth pair and the tuple of stdout
              and stderr returned by processutils.execute invoked with the
              executable script for binding
    :raises: kuryr.common.exceptions.VethCreationFailure,
             kuryr.common.exceptions.DriverNotEnabledException,
             processutils.ProcessExecutionError
    """
    driver = importutils.import_module(
        driver or cfg.CONF.binding.default_driver)
    _verify_driver(driver)

    return driver.port_bind(endpoint_id, port, subnets, network=network,
                            vm_port=vm_port,
                            segmentation_id=segmentation_id,
                            **kwargs)


def port_unbind(endpoint_id, neutron_port, driver=None, **kwargs):
    """Unbinds the Neutron port from the network interface on the host.

    :param endpoint_id: the ID of the Docker container as string
    :param neutron_port: a port dictionary returned from python-neutronclient
    :param driver:       the binding driver name
    :param kwargs:       Additional driver-specific arguments
    :returns: the tuple of stdout and stderr returned by processutils.execute
              invoked with the executable script for unbinding
    :raises: processutils.ProcessExecutionError, pyroute2.NetlinkError,
             kuryr.common.exceptions.DriverNotEnabledException,
    """
    driver = importutils.import_module(
        driver or cfg.CONF.binding.default_driver)
    _verify_driver(driver)

    return driver.port_unbind(endpoint_id, neutron_port, **kwargs)
