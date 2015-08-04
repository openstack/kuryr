===============
Design of Kuryr
===============


What is Kuryr
~~~~~~~~~~~~~

Kuryr implements a `libnetwork remote driver`_ and maps its calls to OpenStack
`Neutron`_. It works as a translator between libnetwork's
`Container Network Model`_ (CNM) and `Neutron's networking model`_.

.. _libnetwork remote driver: https://github.com/docker/libnetwork/blob/master/docs/remote.md
.. _Neutron: https://wiki.openstack.org/wiki/Neutron
.. _Container Network Model: https://github.com/docker/libnetwork/blob/master/docs/design.md#the-container-network-model
.. _Neutron's networking model: https://wiki.openstack.org/wiki/Neutron/APIv2-specification

Goal
----

Through Kuryr any Neutron plugin can communicate with libnetwork. Neutron APIs
are vendor agnostic and thus all Neutron plugins will have the capability of
providing the networking backend of Docker for a similar small plugging snippet
as they have in nova.

Kuryr also takes care of binding one of a veth pair to a network interface on
the host, e.g., Linux bridge, Open vSwitch datapath and so on.

Kuryr Workflow
~~~~~~~~~~~~~~

Kuryr resides in each host that runs Docker containers and serves `APIs`_
required for the libnetwork remote driver.

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

.. _APIs: https://github.com/docker/libnetwork/blob/master/docs/design.md#api
.. _plugin discovery mechanism: https://github.com/docker/docker/blob/master/docs/extend/plugin_api.md#plugin-discovery
.. _Neutron client: http://docs.openstack.org/developer/python-neutronclient/
.. _libkv: https://github.com/docker/libkv

User Workflow
~~~~~~~~~~~~~

1. A user creates a network ``foo``
   ::

       $ sudo docker network create --driver=kuryr foo
       51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1

   This makes a HTTP POST call on ``/NetworkDriver.CraeteNetwork`` with the
   following JSON data.
   ::

        {
            "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1",
            "Options": {
                ...
            }
        }

2. A user creates a service ``bar`` against network ``foo``
   ::

       $ sudo docker network publish service bar.foo
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

3. A user shows information of the service
   ::

       $ sudo docker service info test.bar
       Service Id: db0524fa27184de3dfe274908e77e05155e12e20269c782984468b251fe507d7
               Name: bar
               Network: foo

   This makes a HTTP POST call on ``/NetworkDriver.EndpointOperInfo``

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

7. A user deletes the network
   ::

       $ sudo  docker network rm foo

   This makes a HTTP POST call on ``/NetworkDriver.DeleteNetwork`` with the
   following JSON data.
   ::

       {
           "NetworkID": "51c75a2515d47edecc3f720bb541e287224416fb66715eb7802011d6ffd499f1"
       }

The workflows described in 2., 4., 5. and 6. can be done in the following
single command.::

    $ sudo docker run --publish-service=cont.implicit.foo -itd busybox


Mapping between the CNM and the Neutron's Networking Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kuryr communicates with Neutron via `Neutron client`_ and bridges between
libnetwork and Neutron traslating their networking models. The mapping
between them can be expressed as the following table.

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
