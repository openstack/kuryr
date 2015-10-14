===============================
Libnetwork Remote Driver Design
================================


What is Kuryr
--------------

Kuryr implements a `libnetwork remote driver`_ and maps its calls to OpenStack
`Neutron`_. It works as a translator between libnetwork's
`Container Network Model`_ (CNM) and `Neutron's networking model`_.

Goal
~~~~~

Through Kuryr any Neutron plugin can be used as libnetwork backend with no additional
effort.
Neutron APIs are vendor agnostic and thus all Neutron plugins will have the capability of
providing the networking backend of Docker for a similar small plugging snippet
as they have in nova.

Kuryr also takes care of binding one of a veth pair to a network interface on
the host, e.g., Linux bridge, Open vSwitch datapath and so on.


Kuryr Workflow - Host Networking
---------------------------------
Kuryr resides in each host that runs Docker containers and serves `APIs`_
required for the libnetwork remote driver.
It is planned to use the `Adding tags to resources`_ new Neutron feature by Kuryr,
to map between Neutron resource Id's and Docker Id's (UUID's)

1. libnetwork discovers Kuryr via `plugin discovery mechanism`_

   - During this process libnetwork makes a HTTP POST call on
     ``/Plugin.Active`` and examines if it's a network driver

2. libnetwork registers Kuryr as a remote driver

3. A user makes requests against libnetwork with the driver specifier for Kuryr

   - i.e., ``--driver=kuryr`` or ``-d kuryr`` for the Docker CLI

4. libnetwork makes API calls against Kuryr

5. Kuryr receives the requests and calls Neutron APIs with `Neutron client`_

6. Kuryr receives the responses from Neutron and compose the responses for
   libnetwork

7. Kuryr returns the responses to libnetwork

8. libnetwork stores the returned information to its key/value datastore
   backend

   - the key/value datastore is abstracted by `libkv`_


Libnetwork User Workflow (with Kuryr as remove driver) - Host Networking
-------------------------------------------------------------------------
1. A user creates a network ``foo``
   ::

       $ sudo docker network create --driver=kuryr foo
       51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1

   This makes a HTTP POST call on ``/NetworkDriver.CreateNetwork`` with the
   following JSON data.
   ::

        {
            "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1",
            "Options": {
                ...
            }
        }

   The Kuryr remote driver will then generate a Neutron API request to create an underlying Neutron network.
   When the Neutron network has been created, the Kuryr remote driver will generate an empty success response
   to the docker daemon.
   Kuryr tags the Neutron network with the NetworkID from docker.

2. A user creates a service ``bar`` against network ``foo``
   ::

       $ sudo docker service publish bar.foo
       98953db3f8e6628caf4a7cad3c866cb090654e3dee3e37206ad8c0a81355f1b7

   This makes a HTTP POST call on ``/NetworkDriver.CreateEndpoint`` with the
   following JSON data.
   ::

       {
           "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1",
           "EndpointID": "98953db3f8e6628caf4a7cad3c866cb090654e3dee3e37206ad8c0a81355f1b7",
           "Interfaces": [
               ...
           ],
           "Options": {
               ...
           }
       }

   The Kuryr remote driver then generate a Neutron API request to create a Neutron
   subnet and a port with the matching fields for all interfaces in the request.
   Kuryr needs to create the subnet dynamically as it has no information on
   the interfaces list IP's.

   the following steps are taken:

   1) On the endpoint creation Kuryr examine if there's a subnet which CIDR corresponds to
      Address or AddressIPv6 requested.
   2) If there's a subnet, Kuryr tries to reuse it without creating a new subnet.
      otherwise it create a new one with the given CIDR
   3) If a CIDR is not passed, Kuryr creates a default IPv4 or IPv6 subnets from a
      specific subnet pool.
      more information can be found in Kuryr `IPAM blueprint`_
   4) Kuryr creates a port assigning the IP address to it and associating the port with
      the subnet based on it's already allocated in 2.

   On the subnet creation described in (2) and (3) above, Kuryr tries to grab
   the allocation pool greedily by not specifying ``allocation_pool``. Without
   ``allocation_pool``, Neutron allocates all IP addresses in the range of the
   subnet CIDR as described in `Neutron's API reference`_.

   When the Neutron port has been created, the Kuryr remote driver will generate a response to the
   docker daemon indicating the port's IPv4, IPv6, and Mac addresses as follows.
   ::

        {
            "Interfaces": [{
            "ID": <port-id>,
            "Address": <port-fixed-IP-address>,
            "AddressIPv6": <port-fixed-IPv6-address>,
            "MacAddress": <port-mac-addr>
             }, ...]
        }

   Kuryr tags the Neutron subnet and port with Docker Interface id.

3. A user shows information of the service
   ::

       $ sudo docker service info test.bar
       Service Id: db0524fa27184de3dfe274908e77e05155e12e20269c782984468b251fe507d7
               Name: bar
               Network: foo

4. A user attaches a container to the service
   ::

       $ CID=$(sudo docker run -itd busybox)
       $ sudo docker service attach $CID bar.foo

   or if a network interface needs to be attached to the container before its
   launch,
   ::

       $ sudo docker run --publish-service=bar.foo -itd busybox
       12bbda391ed0728787b2c2131f091f6d5744806b538b9314c15e789e5a1ba047

   This makes a HTTP POST call on ``/NetworkDriver.Join`` with the following
   JOSN data.
   ::

       {
           "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1",
           "EndpointID": "98953db3f8e6628caf4a7cad3c866cb090654e3dee3e37206ad8c0a81355f1b7",
           "SandboxKey": "/var/run/docker/netns/12bbda391ed0",
           "Options": {
               ...
           }
       }

   Kuryr connects the container to the corresponding neutron network by doing the following steps:

   1) Generate a veth pair
   2) Connect one end of the veth pair to the container (which is running in a namespace
      that was created by Docker)
   3) Perform a neutron-port-type-dependent VIF-binding to the corresponding Neutron port
      using the VIF binding layer and depending on the specific port type.

   After the VIF-binding is completed, the Neutron remote driver generate a response to the Docker
   daemon as specified in the libnetwork documentation for a join request.
   (https://github.com/docker/libnetwork/blob/master/docs/remote.md#join)

5. A user detaches the container from the service
   ::

       $ sudo docker service detach $CID bar.foo

   This makes a HTTP POST call on ``/NetworkDriver.Leave`` with the following
   JSON data.
   ::

       {
           "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1",
           "EndpointID": "98953db3f8e6628caf4a7cad3c866cb090654e3dee3e37206ad8c0a81355f1b7"
       }

   Kuryr remote driver will remove the VIF binding between the container and the Neutron port,
   and generate an empty response to the Docker daemon.

6. A user unpublishes the service
   ::

       $ sudo docker unpublish bar.foo

   This makes a HTTP POST call on ``/NetworkDriver.DeleteEndpoint`` with the
   following JSON data.
   ::

       {
           "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1",
           "EndpointID": "98953db3f8e6628caf4a7cad3c866cb090654e3dee3e37206ad8c0a81355f1b7"
       }

   Kuryr remote driver generate a Neutron API request to delete the associated Neutron port,
   in case the relevant port subnet is empty, Kuryr also deletes the subnet object using Neutron API
   and generate an empty response to the Docker daemon: {}

7. A user deletes the network
   ::

       $ sudo  docker network rm foo

   This makes a HTTP POST call on ``/NetworkDriver.DeleteNetwork`` with the
   following JSON data.
   ::

       {
           "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1"
       }

    Kuryr remote driver generate a Neutron API request to delete the corresponding Neutron network.
    When the Neutron network has been deleted, the Kuryr remote driver  generate an empty response
    to the docker daemon: {}

The workflows described in 2., 4., 5. and 6. can be done in the following
single command.::

    $ sudo docker run --publish-service=cont.implicit.foo -itd busybox


Mapping between the CNM and the Neutron's Networking Model
------------------------------------------------------------

Kuryr communicates with Neutron via `Neutron client`_ and bridges between
libnetwork and Neutron by translating their networking models. The following
table depicts the current mapping between libnetwork and Neutron models:

===================== ======================
libnetwork            Neutron
===================== ======================
Network               Network
Sandbox               Subnet, Port and netns
Endpoint              Subnet, Port
===================== ======================

libnetwork's Sandbox and Endpoint can be mapped into Neutron's Subnet and Port,
however, Sandbox is invisible from users directly and Endpoint is only the
visible and editable resource entity attachable to containers from users'
perspective. Sandbox manages information exposed by Endpoint behind the scene
automatically.

.. _libnetwork remote driver: https://github.com/docker/libnetwork/blob/master/docs/remote.md
.. _Neutron: https://wiki.openstack.org/wiki/Neutron
.. _Container Network Model: https://github.com/docker/libnetwork/blob/master/docs/design.md#the-container-network-model
.. _Neutron's networking model: https://wiki.openstack.org/wiki/Neutron/APIv2-specification
.. _Neutron client: http://docs.openstack.org/developer/python-neutronclient/
.. _plugin discovery mechanism: https://github.com/docker/docker/blob/master/docs/extend/plugin_api.md#plugin-discovery
.. _Adding tags to resources: https://review.openstack.org/#/c/216021/
.. _APIs: https://github.com/docker/libnetwork/blob/master/docs/design.md#api
.. _libkv: https://github.com/docker/libkv
.. _IPAM blueprint: https://blueprints.launchpad.net/kuryr/+spec/ipam
.. _Neutron's API reference: http://developer.openstack.org/api-ref-networking-v2.html#createSubnet
