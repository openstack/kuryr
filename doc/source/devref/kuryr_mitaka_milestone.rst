..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=====================================
Kuryr - Milestone for Mitaka
=====================================

https://launchpad.net/kuryr


Kuryr Roles and Responsibilities - First Milestone for Mitaka release
-----------------------------------------------------------------------

This chapter includes the various use cases that Kuryr aims at solving,
some were briefly described in the introduction chapter.
This list of items will need to be prioritized.

1) Deploy Kuryr as a libnetwork remote driver (map between libnetwork
   API and Neutron API)

2) Configuration
   https://etherpad.openstack.org/p/kuryr-configuration

   Includes authentication to Neutron and Docker (Keystone integration)

3) VIF Binding
   https://etherpad.openstack.org/p/Kuryr_vif_binding_unbinding
   https://blueprints.launchpad.net/kuryr/+spec/vif-binding-and-unbinding-mechanism

4) Containerized neutron plugins + Kuryr common layer (Kolla)

5) Nested VM - agent less mode (or with Kuryr shim layer)

   Magnum Kuryr Integration
   https://blueprints.launchpad.net/kuryr/+spec/containers-in-instances

   Create kuryr heat resources for Magnum to consume

7) Missing APIs in Neutron to support docker networking model

   Port-Mapping:
   Docker port-mapping will be implemented in services and not networks
   (libnetwork).
   There is a relationship between the two.
   Here are some details:
   https://github.com/docker/docker/blob/master/experimental/networking.md
   https://github.com/docker/docker/blob/master/api/server/server_experimental_unix.go#L13-L16

   Here is an example of publishing a service on a particular network and attaching
   a container to the service:
   docker service publish db1.prod cid=$(docker run -itd -p 8000:8000 ubuntu)
   docker service attach $cid db1.prod

   Kuryr will need to interact with the services object of the docker
   api to support port-mapping.
   We are planning to propose a port forwarding spec in Mitaka that
   introduces the API and reference implementation of port forwarding
   in Neutron to enable this feature.

   Neutron relevant specs:
   VLAN trunk ports
   ( https://blueprints.launchpad.net/neutron/+spec/vlan-aware-vms)
   (Used for nested VM's defining trunk port and sub-ports)

   DNS resolution according to port name
   (https://review.openstack.org/#/c/90150/)
   (Needed for feature compatibility with Docker services publishing)

8) Mapping between Neutron identifiers and Docker identifiers

   A new spec in Neutron is being proposed that we can
   leverage for this use case: `Adding tags to resources`_ .
   Tags are similar in concept to Docker labels.

9) Testing (CI)

   There should be a testing infrastructure running both unit and functional tests with full
   setup of docker + kuryr + neutron.

10) Packaging and devstack plugin for Kuryr


Kuryr Future Scope
------------------

1) Kuryr is planned to support other networking backend models defined by Kubernetes
   (and not just libnetwork).

2) In addition to Docker, services are a key component of Kubernetes.
   In Kubernetes, I create a pod and optionally create/attach a service to a pod:
   https://github.com/kubernetes/kubernetes/blob/master/docs/user-guide/services.md

   Services could be implemented with LBaaS APIs

   An example project that does this for Kubernetes and Neutron LBaaS:
   https://github.com/kubernetes/kubernetes/blob/release-1.0/pkg/cloudprovider/openstack/openstack.go


References
==========

.. _libnetwork remote driver: https://github.com/docker/libnetwork/blob/master/docs/remote.md
.. _Neutron: https://wiki.openstack.org/wiki/Neutron
.. _Container Network Model: https://github.com/docker/libnetwork/blob/master/docs/design.md#the-container-network-model
.. _Neutron's networking model: https://wiki.openstack.org/wiki/Neutron/APIv2-specification
.. _Magnum: https://wiki.openstack.org/wiki/Magnum
.. _OVN: https://launchpad.net/networking-ovn
.. _Kolla: https://wiki.openstack.org/wiki/Kolla
.. _APIs: https://github.com/docker/libnetwork/blob/master/docs/design.md#api
.. _plugin discovery mechanism: https://github.com/docker/docker/blob/master/docs/extend/plugin_api.md#plugin-discovery
.. _Neutron client: http://docs.openstack.org/developer/python-neutronclient/
.. _libkv: https://github.com/docker/libkv
.. _VIF binding: https://blueprints.launchpad.net/kuryr/+spec/vif-binding-and-unbinding-mechanism
.. _Adding tags to resources: https://review.openstack.org/#/c/216021/
.. _User labels in docker patch: https://github.com/docker/libnetwork/pull/222/files#diff-2b9501381623bc063b38733c35a1d254
