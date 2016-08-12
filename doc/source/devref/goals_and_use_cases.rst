===================
Goals And Use Cases
===================

Kuryr provides networking to Docker containers by leveraging the Neutron APIs
and services. It also provides containerized images for common Neutron plugins

Kuryr implements a `libnetwork remote driver <https://github.com/docker/libnetwork/blob/master/docs/remote.md>`_
and maps its calls to OpenStack `Neutron <https://wiki.openstack.org/wiki/Neutron>`_.
It works as a translator between libnetwork's
`Container Network Model <https://github.com/docker/libnetwork/blob/master/docs/design.md#the-container-network-model>`_ (CNM)
and `Neutron's networking model <https://wiki.openstack.org/wiki/Neutron/APIv2-specification>`_
and provides container-host or container-vm (nested VM) binding.

Using Kuryr any Neutron plugin can be used as a libnetwork remote driver
explicitly. Neutron APIs are vendor agnostic and thus all Neutron plugins will
have the capability of providing the networking backend of Docker with a common
lightweight plugging snippet as they have in nova.

Kuryr takes care of binding the container namespace to the networking
infrastructure by providing a generic layer for `VIF binding <https://blueprints.launchpad.net/kuryr/+spec/vif-binding-and-unbinding-mechanism>`_
depending on the port type for example Linux bridge port, Open vSwitch port,
Midonet port and so on.

Kuryr should be the gateway between containers networking API and use cases and
Neutron APIs and services and should bridge the gaps between the two in both
domains. It will map the missing parts in Neutron and drive changes to adjust
it.

Kuryr should address `Magnum <https://wiki.openstack.org/wiki/Magnum>`_ project
use cases in terms of containers networking and serve as a unified interface for
Magnum or any other OpenStack project that needs to leverage containers
networking through Neutron API.
In that regard, Kuryr aims at leveraging Neutron plugins that support VM
nested container's use cases and enhancing Neutron APIs to support these cases
(for example `OVN <https://launchpad.net/networking-ovn>`_).
An etherpad regarding `Magnum Kuryr Integration <https://etherpad.openstack.org/p/magnum-kuryr>`_
describes the various use cases Kuryr needs to support.

Kuryr should provide containerized Neutron plugins for easy deployment and must
be compatible with OpenStack `Kolla <https://wiki.openstack.org/wiki/Kolla>`_
project and its deployment tools. The containerized plugins have the common
Kuryr binding layer which binds the container to the network infrastructure.

Kuryr should leverage Neutron sub-projects and services (in particular LBaaS,
FWaaS, VPNaaS) to provide to support advanced containers networking use cases
and to be consumed by containers orchestration management systems (for example
Kubernetes , or even OpenStack Magnum).

Kuryr also support pre-allocating of networks, ports and subnets, and binding
them to Docker networks/endpoints upon creation depending on specific labels
that are passed during Docker creation. There is a patch being merged in Docker
to support providing user labels upon network creation. you can look at this
`User labels in docker patch <https://github.com/docker/libnetwork/pull/222/files#diff-2b9501381623bc063b38733c35a1d254>`_.
