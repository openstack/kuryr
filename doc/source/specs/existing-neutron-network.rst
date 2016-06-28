..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

======================================
Reuse of the existing Neutron networks
======================================

https://blueprints.launchpad.net/kuryr/+spec/existing-neutron-network

The current Kuryr implementation assumes the Neutron networks, subnetpools,
subnets and ports are created by Kuryr and their lifecycles are completely
controlled by Kuryr. However, in the case where users need to mix the VM
instances and/or the bare metal nodes with containers, the capability of
reusing existing Neutron networks for implementing Kuryr networks becomes
valuable.


Problem Description
-------------------

The main use case being addressed in this spec is described below:

* Use of existing Neutron network and subnet resources created independent of
  Kuryr

With the addition of Tags to neutron resources
`Add tags to neutron resources spec`_
the association between container networks and Neutron networks is
implemented by associating tag(s) to Neutron networks.  In particular,
the container network ID is stored in such tags.  Currently the
maximum size for tags is 64 bytes. Therefore, we currently use two
tags for each network to store the corresponding Docker ID.


Proposed Change
---------------

This specification proposes to use the ``Options`` that can be specified by
user during the creation of Docker networks.  We propose to use either the
Neutron network uuid or name to identify the Neutron network to use.  If the
Neutron network uuid or name is specified but such a network does not exist or
multiple such networks exist in cases where a network name is specified, the
create operation fails. Otherwise, the existing network will be used.
Similarly, if a subnet is not associated with the existing network it will be
created by Kuryr. Otherwise, the existing subnet will be used.

The specified Neutron network is tagged with a well known string such that it
can be verified whether it already existed at the time of the creation of the
Docker network or not.


.. NOTE(banix): If a Neutron network is specified but it is already
   associated with an existing Kuryr network we may refuse the request
   unless there are use cases which allow the use of a Neutron network
   for realizing more than one Docker networks.


.. _workflow:

Proposed Workflow
~~~~~~~~~~~~~~~~~

1. A user creates a Docker network and binds it to an existing Neutron network
   by specifying it's uuid:
   ::

       $ sudo docker network create --driver=kuryr --ipam-driver=kuryr \
              --subnet 10.0.0.0/16 --gateway 10.0.0.1 --ip-range 10.0.0.0/24 \
              -o neutron.net.uuid=25495f6a-8eae-43ff-ad7b-77ba57ed0a04 \
              foo
       286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364

       $ sudo docker network create --driver=kuryr --ipam-driver=kuryr \
              --subnet 10.0.0.0/16 --gateway 10.0.0.1 --ip-range 10.0.0.0/24 \
              -o neutron.net.name=my_network_name \
              foo
       286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364

   This creates a Docker network with the given name, ``foo`` in this case, by
   using the Neutron network with the specified uuid or name.

   If subnet information is specified by ``--subnet``, ``--gateway``, and
   ``--ip-range`` as shown in the command above, the corresponding subnetpools
   and subnets are created or the existing resources are appropriately reused
   based on the provided information such as CIDR. For instance, if the network
   with the given UUID in the command exists and that network has the subnet
   whose CIDR is the same as what is given by ``--subnet`` and possibly
   ``--ip-range``, Kuryr doesn't create a subnet and just leaves the existing
   subnets as they are. Kuryr composes the response from the information of
   the created or reused subnet.

   It is expected that when Kuryr driver is used, the Kuryr IPAM driver is also
   used.

   If the gateway IP address of the reused Neutron subnet doesn't match with
   the one given by ``--gateway``, Kuryr returns the IP address set in the
   Neutron subnet nevertheless and the command is going to fail because of
   Dockers's validation against the response.

2. A user inspects the created Docker network
   ::

       $ sudo docker network inspect foo
       {
           "Name": "foo",
           "Id": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
           "Scope": "global",
           "Driver": "kuryr",
           "IPAM": {
               "Driver": "kuryr",
               "Config": [{
                   "Subnet": "10.0.0.0/16",
                   "IPRange": "10.0.0.0/24",
                   "Gateway": "10.0.0.1"
               }]
           },
           "Containers": {}
           "Options": {
               "com.docker.network.generic": {
                   "neutron.net.uuid": "25495f6a-8eae-43ff-ad7b-77ba57ed0a04"
               }
           }
       }

   A user can see the Neutron ``uuid`` given in the command is stored in the
   Docker's storage and can be seen by inspecting the network.

3. A user launches a container and attaches it to the network
   ::

       $ CID=$(sudo docker run --net=foo -itd busybox)

   This process is identical to the existing logic described in `Kuryr devref`_.
   libnetwork calls ``/IpamDriver.RequestAddress``,
   ``/NetworkDriver.CreateEndpoint`` and then ``/NetworkDriver.Join``. The
   appropriate available IP address shall be returned by Neutron through Kuryr
   and a port with the IP address is created under the subnet on the network.

4. A user terminates the container
   ::

       $ sudo docker kill ${CID}

   This process is identical to the existing logic described in `Kuryr devref`_
   as well. libnetwork calls ``/IpamDriver.ReleaseAddress``,
   ``/NetworkDriver.Leave`` and then ``/NetworkDriver.DeleteEndpoint``.

5. A user deletes the network
   ::

       $ sudo docker network rm foo

   When an existing Neutron network is used to create a Docker network, it is
   tagged such that during the delete operation the Neutron network does not
   get deleted.  Currently, if an existing Neutron network is used, the subnets
   associated with it (whether pre existing or newly created) are preserved as
   well. In the future, we may consider tagging subnets themselves or the
   networks (with subnet information) to decide whether a subnet is to be
   deleted or not.


Challenges
----------

None

References
----------

* `Add tags to neutron resources spec`_

.. _Add tags to neutron resources spec: http://docs.openstack.org/developer/neutron/devref/tag.html
.. _Kuryr devref: http://docs.openstack.org/developer/kuryr/devref/index.html
