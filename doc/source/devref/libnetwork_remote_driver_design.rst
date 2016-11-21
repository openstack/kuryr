=======================================
Libnetwork Remote Network Driver Design
=======================================

What is Kuryr
-------------

Kuryr implements a `libnetwork remote network driver <https://github.com/docker/libnetwork/blob/master/docs/remote.md>`_
and maps its calls to OpenStack `Neutron <https://wiki.openstack.org/wiki/Neutron>`_.
It works as a translator between libnetwork's `Container Network Model <https://github.com/docker/libnetwork/blob/master/docs/design.md#the-container-network-model>`_ (CNM) and `Neutron's networking model <https://wiki.openstack.org/wiki/Neutron/APIv2-specification>`_.
Kuryr also acts as a `libnetwork IPAM driver <https://github.com/docker/libnetwork/blob/master/docs/ipam.md>`_.

Goal
~~~~

Through Kuryr any Neutron plugin can be used as libnetwork backend with no
additional effort. Neutron APIs are vendor agnostic and thus all Neutron
plugins will have the capability of providing the networking backend of Docker
for a similar small plugging snippet as they have in nova.

Kuryr also takes care of binding one of a veth pair to a network interface on
the host, e.g., Linux bridge, Open vSwitch datapath and so on.


Kuryr Workflow - Host Networking
--------------------------------
Kuryr resides in each host that runs Docker containers and serves `APIs <https://github.com/docker/libnetwork/blob/master/docs/design.md#api>`_
required for the libnetwork remote network driver. It is planned to use the
`Adding tags to resources <https://review.openstack.org/#/c/216021/>`_
new Neutron feature by Kuryr, to map between
Neutron resource Id's and Docker Id's (UUID's)

1. libnetwork discovers Kuryr via `plugin discovery mechanism <https://github.com/docker/docker/blob/master/docs/extend/plugin_api.md#plugin-discovery>`_ *before the first request is made*

   - During this process libnetwork makes a HTTP POST call on
     ``/Plugin.Activate`` and examines the driver type, which defaults to
     ``"NetworkDriver"`` and ``"IpamDriver"``
   - libnetwork also calls the following two API endpoints

     1. ``/NetworkDriver.GetCapabilities`` to obtain the capability of Kuryr
        which defaults to ``"local"``
     2. ``/IpamDriver.GetDefaultAddressSpcaces`` to get the default address
        spaces used for the IPAM

2. libnetwork registers Kuryr as a remote driver

3. A user makes requests against libnetwork with the network driver specifier for Kuryr

   - i.e., ``--driver=kuryr`` or ``-d kuryr`` **and** ``--ipam-driver=kuryr``
     for the Docker CLI

4. libnetwork makes API calls against Kuryr

5. Kuryr receives the requests and calls Neutron APIs with `Neutron client <http://docs.openstack.org/developer/python-neutronclient/>`_

6. Kuryr receives the responses from Neutron and compose the responses for
   libnetwork

7. Kuryr returns the responses to libnetwork

8. libnetwork stores the returned information to its key/value datastore
   backend

   - the key/value datastore is abstracted by `libkv <https://github.com/docker/libkv>`_


Libnetwork User Workflow (with Kuryr as remote network driver) - Host Networking
---------------------------------------------------------------------------------
1. A user creates a network ``foo`` with the subnet information::

       $ sudo docker network create --driver=kuryr --ipam-driver=kuryr \
         --subnet 10.0.0.0/16 --gateway 10.0.0.1 --ip-range 10.0.0.0/24 foo
       286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364

   This makes a HTTP POST call on ``/IpamDriver.RequestPool`` with the following
   JSON data::

       {
           "AddressSpace": "global_scope",
           "Pool": "10.0.0.0/16",
           "SubPool": "10.0.0.0/24",
           "Options": null
           "V6": false
       }

   The value of ``SubPool`` comes from the value specified in ``--ip-range``
   option in the command above and value of ``AddressSpace`` will be ``global_scope`` or ``local_scope`` depending on value of ``capability_scope`` configuration option. Kuryr creates a subnetpool, and then returns
   the following response::

       {
           "PoolID": "941f790073c3a2c70099ea527ee3a6205e037e84749f2c6e8a5287d9c62fd376",
           "Pool": "10.0.0.0/16",
           "Data": {}
       }

   If the ``--gateway`` was specified like the command above, another HTTP POST
   call against ``/IpamDriver.RequestAddress`` follows with the JSON data below::

       {
           "Address": "10.0.0.1",
           "PoolID": "941f790073c3a2c70099ea527ee3a6205e037e84749f2c6e8a5287d9c62fd376",
           "Options": null,
       }

   As the IPAM driver Kuryr allocates a requested IP address and returns the
   following response::

       {
           "Address": "10.0.0.1/16",
           "Data": {}
       }

   Finally a HTTP POST call on ``/NetworkDriver.CreateNetwork`` with the
   following JSON data::

        {
            "NetworkID": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
            "IPv4Data": [{
                "Pool": "10.0.0.0/16",
                "Gateway": "10.0.0.1/16",
                "AddressSpace": ""
            }],
            "IPv6Data": [],
            "Options": {"com.docker.network.generic": {}}
        }

   The Kuryr remote network driver will then generate a Neutron API request to
   create subnet with pool cidr and an underlying Neutron network. When the
   Neutron subnet and network has been created, the Kuryr remote network driver
   will generate an empty success response to the docker daemon. Kuryr tags the
   Neutron network with the NetworkID from docker.

2. A user launches a container against network ``foo``::

       $ sudo docker run --net=foo -itd --name=container1 busybox
       78c0458ba00f836f609113dd369b5769527f55bb62b5680d03aa1329eb416703

   This makes a HTTP POST call on ``/IpamDriver.RequestAddress`` with the
   following JSON data::

        {
            "Address": "",
            "PoolID": "941f790073c3a2c70099ea527ee3a6205e037e84749f2c6e8a5287d9c62fd376",
            "Options": null,
        }

   The IPAM driver Kuryr sends a port creation request to neutron and returns the following response with neutron provided ip address::

       {
           "Address": "10.0.0.2/16",
           "Data": {}
       }


   Then another HTTP POST call on ``/NetworkDriver.CreateEndpoint`` with the
   following JSON data is made::

        {
            "NetworkID": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
            "Interface": {
                "AddressIPv6": "",
                "MacAddress": "",
                "Address": "10.0.0.2/16"
            },
            "Options": {
                "com.docker.network.endpoint.exposedports": [],
                "com.docker.network.portmap": []
            },
            "EndpointID": "edb23d36d77336d780fe25cdb5cf0411e5edd91b0777982b4b28ad125e28a4dd"
        }

   The Kuryr remote network driver then generates a Neutron API request to
   fetch port with the matching fields for interface in the request. Kuryr
   then updates this port's name, tagging it with endpoint ID.

   Following steps are taken:

   1) On the endpoint creation Kuryr examines if there's a Port with CIDR
      that corresponds to Address or AddressIPv6 requested.
   2) If there's a Port, Kuryr tries to reuse it without creating a new
      Port. Otherwise it creates a new one with the given address.
   3) Kuryr tags the Neutron port with EndpointID.

   When the Neutron port has been updated, the Kuryr remote driver will
   generate a response to the docker daemon in following form:
   (https://github.com/docker/libnetwork/blob/master/docs/remote.md#create-endpoint)::

        {
            "Interface": {"MacAddress": "08:22:e0:a8:7d:db"}
        }


   On receiving success response, libnetwork makes a HTTP POST call on ``/NetworkDriver.Join`` with
   the following JSON data::

        {
            "NetworkID": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
            "SandboxKey": "/var/run/docker/netns/052b9aa6e9cd",
            "Options": null,
            "EndpointID": "edb23d36d77336d780fe25cdb5cf0411e5edd91b0777982b4b28ad125e28a4dd"
        }

   Kuryr connects the container to the corresponding neutron network by doing
   the following steps:

   1) Generate a veth pair.
   2) Connect one end of the veth pair to the container (which is running in a
      namespace that was created by Docker).
   3) Perform a neutron-port-type-dependent VIF-binding to the corresponding
      Neutron port using the VIF binding layer and depending on the specific
      port type.

   After the VIF-binding is completed, the Kuryr remote network driver
   generates a response to the Docker daemon as specified in the libnetwork
   documentation for a join request.
   (https://github.com/docker/libnetwork/blob/master/docs/remote.md#join)

3. A user requests information about the network::

       $ sudo docker network inspect foo
        {
            "Name": "foo",
            "Id": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
            "Scope": "local",
            "Driver": "kuryr",
            "IPAM": {
                "Driver": "default",
                "Config": [{
                    "Subnet": "10.0.0.0/16",
                    "IPRange": "10.0.0.0/24",
                    "Gateway": "10.0.0.1"
                }]
            },
            "Containers": {
                "78c0458ba00f836f609113dd369b5769527f55bb62b5680d03aa1329eb416703": {
                    "endpoint": "edb23d36d77336d780fe25cdb5cf0411e5edd91b0777982b4b28ad125e28a4dd",
                    "mac_address": "02:42:c0:a8:7b:cb",
                    "ipv4_address": "10.0.0.2/16",
                    "ipv6_address": ""
                }
            }
        }


4. A user connects one more container to the network::

       $ sudo docker network connect foo container2
        d7fcc280916a8b771d2375688b700b036519d92ba2989622627e641bdde6e646

       $ sudo docker network inspect foo
        {
            "Name": "foo",
            "Id": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
            "Scope": "local",
            "Driver": "kuryr",
            "IPAM": {
                "Driver": "default",
                "Config": [{
                    "Subnet": "10.0.0.0/16",
                    "IPRange": "10.0.0.0/24",
                    "Gateway": "10.0.0.1"
                }]
            },
            "Containers": {
                "78c0458ba00f836f609113dd369b5769527f55bb62b5680d03aa1329eb416703": {
                    "endpoint": "edb23d36d77336d780fe25cdb5cf0411e5edd91b0777982b4b28ad125e28a4dd",
                    "mac_address": "02:42:c0:a8:7b:cb",
                    "ipv4_address": "10.0.0.2/16",
                    "ipv6_address": ""
                },
                "d7fcc280916a8b771d2375688b700b036519d92ba2989622627e641bdde6e646": {
                    "endpoint": "a55976bafaad19f2d455c4516fd3450d3c52d9996a98beb4696dc435a63417fc",
                    "mac_address": "02:42:c0:a8:7b:cc",
                    "ipv4_address": "10.0.0.3/16",
                    "ipv6_address": ""
                }
            }
        }


5. A user disconnects a container from the network::

       $ CID=d7fcc280916a8b771d2375688b700b036519d92ba2989622627e641bdde6e646
       $ sudo docker network disconnect foo $CID

   This makes a HTTP POST call on ``/NetworkDriver.Leave`` with the following
   JSON data::

       {
           "NetworkID": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
           "EndpointID": "a55976bafaad19f2d455c4516fd3450d3c52d9996a98beb4696dc435a63417fc"
       }

   Kuryr remote network driver will remove the VIF binding between the
   container and the Neutron port, and generate an empty response to the
   Docker daemon.

   Then libnetwork makes a HTTP POST call on ``/NetworkDriver.DeleteEndpoint`` with the
   following JSON data::

       {
           "NetworkID": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364",
           "EndpointID": "a55976bafaad19f2d455c4516fd3450d3c52d9996a98beb4696dc435a63417fc"
       }

   Kuryr remote network driver generates a Neutron API request to delete the
   associated Neutron port, in case the relevant port subnet is empty, Kuryr
   also deletes the subnet object using Neutron API and generate an empty
   response to the Docker daemon::

       {}

   Finally libnetwork makes a HTTP POST call on ``/IpamDriver.ReleaseAddress``
   with the following JSON data::

       {
           "Address": "10.0.0.3",
           "PoolID": "941f790073c3a2c70099ea527ee3a6205e037e84749f2c6e8a5287d9c62fd376"
       }

   Kuryr remote IPAM driver generates a Neutron API request to delete the associated Neutron port.
   As the IPAM driver Kuryr deallocates the IP address and returns the following response::

       {}

6. A user deletes the network::

       $ sudo docker network rm foo

   This makes a HTTP POST call against ``/NetworkDriver.DeleteNetwork`` with the
   following JSON data::

       {
           "NetworkID": "286eddb51ebca09339cb17aaec05e48ffe60659ced6f3fc41b020b0eb506d364"
       }

   Kuryr remote network driver generates a Neutron API request to delete the
   corresponding Neutron network and subnets. When the Neutron network and subnets has been deleted,
   the Kuryr remote network driver  generate an empty response to the docker
   daemon: {}

   Then another HTTP POST call on ``/IpamDriver.ReleasePool`` with the
   following JSON data is made::

       {
           "PoolID": "941f790073c3a2c70099ea527ee3a6205e037e84749f2c6e8a5287d9c62fd376"
       }

   Kuryr delete the corresponding subnetpool and returns the following response::

       {}

Mapping between the CNM and the Neutron's Networking Model
----------------------------------------------------------

Kuryr communicates with Neutron via `Neutron client <http://docs.openstack.org/developer/python-neutronclient/>`_
and bridges between libnetwork and Neutron by translating their networking models.
The following table depicts the current mapping between libnetwork and Neutron models:

===================== ======================
libnetwork            Neutron
===================== ======================
Network               Network
Sandbox               Subnet, Port and netns
Endpoint              Port
===================== ======================

libnetwork's Sandbox and Endpoint can be mapped into Neutron's Subnet and Port,
however, Sandbox is invisible from users directly and Endpoint is only the
visible and editable resource entity attachable to containers from users'
perspective. Sandbox manages information exposed by Endpoint behind the scene
automatically.


Notes on implementing the libnetwork remote driver API in Kuryr
---------------------------------------------------------------

1. DiscoverNew Notification:
   Neutron does not use the information related to discovery of new resources such
   as new nodes and therefore the implementation of this API method does nothing.

2. DiscoverDelete Notification:
   Neutron does not use the information related to discovery of resources such as
   nodes being deleted and therefore the implementation of this API method does
   nothing.
