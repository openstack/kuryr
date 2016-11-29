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


class KuryrException(Exception):
    """Default Kuryr exception"""


class BindingFailure(KuryrException):
    """Exception represents the binding is failed.

    This exception is thrown when the executable script for the binding is
    failed and Kuryr can't proceed further.
    """


class BindingNotSupportedFailure(KuryrException):
    """Exception represents the vif type binding not support.

    This exception is thrown when the executable script for the binding does
    not exist and Kuryr can't proceed further.
    """


class DuplicatedResourceException(KuryrException):
    """Exception represents there're multiple resources for the ID.

    For example, this exception is thrown when you query the Neutron resource
    associated with the ID and you get multiple resources.
    """


class GatewayConflictFailure(KuryrException):
    """Exception represents gateway ip is conflict.

    This exception is thrown when request gateway ip is conflict with the
    gateway ip in existed network.
    """


class MandatoryApiMissing(KuryrException):
    """Exception represents that mandatory api is not found.

    For example, this exception is thrown when expected neutron
    extension(subnetpools) APIs are not found.
    """


class NoResourceException(KuryrException):
    """Exception represents there's no resource for the given query.

    This exception is thrown when you query the Neutron resource associated
    with the given query and you get none of them actually.
    """


class InactiveResourceException(KuryrException):
    """Exception represents the resource for the given query is not active.

    This exception is thrown when you query the Neutron resource associated
    with the given query and you get the status of the resource as something
    other than ACTIVE.
    """


class VethCreationFailure(KuryrException):
    """Exception represents the veth pair creation is failed.

    This exception is thrown when the veth pair is not created appropriately
    and Kuryr can't proceed the binding further.
    """


class VethDeletionFailure(KuryrException):
    """Exception represents the veth pair deletion is failed.

    This exception is thrown when the veth pair is not deleted appropriately
    and Kuryr can't proceed the unbinding further.
    """


class ExportPortFailure(KuryrException):
    """Exception represents setting up exported port is failed.

    This exception is thrown when performing Neutron security group failed
    for an exported port and Kuryr can't proceed the expose further.
    """


class SegmentationIdAllocationFailure(KuryrException):
    """Exception represents when segmentation id could not be allocated.

    This exception is thrown when the segmentaion id for the isolation of
    container traffic could not be allocated and Kuryr can't proceed further.
    """


class SegmentationDriverBindingDriverCompatibilityFailure(KuryrException):
    """Exception represents when no segmentation type driver is loaded.

    This exception is thrown when configured binding driver does not have
    a supporting segmentation type driver.
    """
