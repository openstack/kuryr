..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================================================================
Networking for Nested Containers in OpenStack / Magnum - Neutron Integration
============================================================================

Launchpad blueprint:

https://blueprints.launchpad.net/kuryr/+spec/containers-in-instances

This blueprint proposes how to integrate Magnum with Neutron based
networking and how the problem of networking for nested containers
can be solved.


Problem Description
===================

Magnum (containers-as-a-service for OpenStack) provisions containers
inside Nova instances and those instances use standard Neutron
networking. These containers are referred to as nested containers.
Currently, there is no integration between Magnum resources and
Neutron and the nested containers are served networking outside
of that provided by OpenStack (Neutron) today.

Definitions
-----------

COE
  Container Orchestration Engine

Bay
  A Magnum resource that includes at least one host to run containers on,
  and a COE to manage containers created on hosts within the bay.

Baymodel
  An object that stores template information about the bay which is
  used to create new bays consistently.

Pod
  Is the smallest deployable unit that can be created, scheduled, and
  managed within Kubernetes.

deviceowner (in Neutron ports)
  device_owner is an attribute which is used internally by Neutron.
  It identifies the service which manages the port. For example
  router interface, router gateway will have their respective
  device owners entries. Similarly, Neutron ports attached to Nova
  instances have device_owner as compute.


Requirements
------------

Following are the requirements of Magnum around networking:

1. Provide networking capabilities to containers running in Nova
   instances.

2. Magnum uses Heat to orchestrate multi-tenant application container
   environments. Heat uses user-data scripts underneath. Therefore,
   Kuryr must have the ability to be deployed/orchestrated using Heat
   via the scripts.

3. Current Magnum container networking implementations such as Flannel,
   provide networking connectivity to containers that reside across
   multiple Nova instances. Kuryr must provide multi-instance container
   networking capabilities. The existing networking capabilities like
   Flannel that Magnum uses will remain and Kuryr to be introduced
   in parallel. Decision on default is for later and default may vary
   based on the type of Magnum Bay. Magnum currently supports three
   types of Bays: Swarm, Kubernetes, and Mesos. They are
   referred to as COEs (Container Orchestration Engine).

4. Kuryr must provide a simple user experience like "batteries included
   but replaceable" philosophy. Magnum must have the ability to deploy
   Kuryr without any user intervention, but allow more advanced users
   to modify Kuryr's default settings as needed.

5. If something needs to be installed in the Nova VMs used by Magnum,
   it needs to be installed in the VMs in a secure manner.

6. Communication between Kuryr and other services must be secure. For example,
   if there is a Kuryr agent running inside the Nova instances, the
   communication between Kuryr components (Kuryr, Kuryr Agent),
   Neutron-Kuryr, Magnum-Kuryr should all be secure.

7. Magnum Bays (Swarm, Kubernetes, etc..) must work the same or
   better than they do with existing network providers such as Flannel.

8. Kuryr must scale just as well, if not better, than existing container
   networking providers.


Use cases
----------

* Any container within a nova instance (VM, baremetal, container)
  may communicate with any other nova instance (VM, baremetal, container),
  or container therein, regardless if the containers are on the same nova
  instance, same host, or different hosts within the same Magnum bay.
  Such containers shall be able to communicate with any OpenStack cloud
  resource in the same Neutron network as the Magnum bay nodes, including
  (but not limited to) Load Balancers, Databases, and other Nova instances.

* Any container should be able to have access to any Neutron resource and
  it's capabilities. Neutron resources include DHCP, router, floating IPs etc.


Proposed Change
===============

The proposal is to leverage the concept of VLAN aware VMs/Trunk Ports [2],
that would be able to discriminate the traffic coming from VM by using
VLAN tags. The trunk port would get attached to a VM and be capable of
receiving both untagged and tagged traffic. Each VLAN would be represented
by a sub port (Neutron ports). A subport must have a network attached.
Each subport will have an additional parameter of VID. VID can be of
different types and VLAN is one of the options.

Each VM running containers by Magnum would need to have a Kuryr container
agent [3]. Kuryr container agent would be like a CNI/CNM plugin, capable of
assigning IPs to the container interfaces and tagging with VLAN IDs.
Magnum baymodel resource can be passed along information for
network type and kuryr will serve Neutron networking. Based on the baymodel,
Magnum can provision necessary services inside the Nova instance using Heat
templates and the scripts Heat uses. The Kuryr container agent would be
responsible for providing networking to the nested containers by tagging
each container interface with a VLAN ID. Kuryr container agent [3] would be
agnostic of COE type and will have different modes based on the COE.
First implementation would support Swarm and the corresponding container
network model via libnetwork.

There are two mechanisms in which nested containers will be served networking
via Kuryr:

1. When user interacts with Magnum APIs to provision containers.
2. Magnum allows end-users to access native COE APIs. It means end-users
   can alternatively create containers using docker CLI etc. If the
   end-users interact with the native APIs, they should be able to get
   the same functionality that is available via Magnum interfaces/orchestration.
   COEs use underlying container runtimes tools so this option is also applicable
   for non-COE APIs as well.

For the case, where user interacts with Magnum APIs, Magnum would need to
integrate a 'network' option in the container API to choose Neutron networks
for containers. This option will be applicable for baymodels
running kuryr type networking. For each container launched, Magnum would
pick up a network, and talk to the COE to provision the container(s), Kuryr agent
would be running inside the Nova instance as a driver/plugin to COE networking
model and based on the network UUID/name, Kuryr agent will create a subport on
parent trunk port, where Nova instance is attached to, Kuryr will allocate
a VLAN ID and subport creation be invoked in Neutron and that will allocate the
IP address. Based on the information returned, Kuryr agent will assign IP to
the container/pod and assign a VLAN, which would match VLAN in the subport
metadata. Once the sub-port is provisioned, it will have an IP address and a
VLAN ID allocated by Neutron and Kuryr respectively.

For the case, where native COE APIs are used, user would be required to specify
information about Kuryr driver and Neutron networks when launching containers.
Kuryr agent will take care of providing networking to the containers in exactly
the same fashion as it would when Magnum talks to the COEs.

Now, all the traffic coming from the containers inside the VMs would be
tagged and backend implementation of how those containers communicate
will follow a generic onboarding mechanism. Neutron supports several plugins
and each plugin uses some backend technology. The plugins would be
responsible for implementing VLAN aware VMs Neutron extension and onboard
the container based on tenant UUID, trunk port ID, VLAN ID, network UUID
and sub-port UUID. Subports will have deviceowner=kuryr. At this
point, a plugin can onboard the container using unique classification per
tenant to the relevant Neutron network and nested container would be
onboarded onto Neutron networks and will be capable of passing packets.
The plugins/onboarding engines would be responsible for tagging the packets
with the correct VLAN ID on their way back to the containers.


Integration Components
-----------------------

Kuryr:

Kuryr and Kuryr Agent will be responsible for providing the networking
inside the Nova instances. Kuryr is the main service/utility running
on the controller node and capabilities like segmentation ID allocation
will be performed there. Kuryr agent will be like a CNI/CNM plugin,
capable of allocating IPs and VLANs to container interfaces. Kuryr
agent will be a helper running inside the Nova instances that can
communicate with Neutron endpoint and Kuryr server. This will require
availability of credentials inside the Bay that Kuryr can use to
communicate. There is a security impact of storing credentials and
it is discussed in the Security Impact section of this document.

More details on the Kuryr Agent can be found here [3].


Neutron:

vlan-aware-vms and notion of trunk port, sub-ports from Neutron will be
used in this design. Neutron will be responsible for all the backend
networking that Kuryr will expose via its mechanisms.

Magnum:

Magnum will be responsible for launching containers on specified/pre-provisioned
networks, using Heat to provisioning Kuryr components inside Nova instances and passing
along network information to the COEs, which can invoke their networking part.

Heat:

Heat templates use use-data scripts to launch tools for containers that Magnum
relies on. The scripts will be updated to handle Kuryr. We should not expect
to run scripts each time a container is started. More details can be
found here [4].

Example of model::

    +-------------------------------+   +-------------------------------+
    | +---------+       +---------+ |   | +---------+       +---------+ |
    | |   c1    |       |   c2    | |   | |   c3    |       |    c4   | |
    | +---------+       +---------+ |   | +---------+       +---------+ |
    |                               |   |                               |
    |              VM1              |   |              VM2              |
    |                               |   |                               |
    |                               |   |                               |
    +---------+------------+--------+   +---------+------------+--------+
              |Trunk Port1 |                      |Trunk Port2 |
              +------------+                      +------------+
                    /|\                                /|\
                   / | \                              / | \
                  /  |  \                            /  |  \
              +--+ +-++ +--+                     +--+ +-++ +--+
              |S1| |S2| |S3|                     |S4| |S5| |S6|
              +-++ +--+ +-++                     +--+ +-++ +-++
                |         |                         |   |    |
                |    |    |                     +---+   |    |
                |    |    +---+N1+          +-+N2+-----------+
                |    |        |  |          |           |
                +-------------+  |          |           |
                     |           |          |           |
                     +           ++ x  x  +-+           +
                     N3+--------+x        x+-----------+N4
                                x          x
                                x  Router  x
                                 x        x
                                    x  x


    C1-4 = Magnum containers
    N1-4 = Neutron Networks and Subnets
    S1,S3,S4,S6 = Subports
    S2,S5 = Trunk ports (untagged traffic)

In the example above, Magnum launches four containers (c1, c2, c3, c4)
spread across two Nova instances. There are four Neutron
networks(N1, N2, N3, N4) in the deployment and all of them are
connected to a router. Both the Nova instances (VM1 and VM2) have one
NIC each and a corresponding trunk port. Each trunk port has three
sub-ports: S1, S2, S3 and S4, S5, S6 for VM1 and VM2 respectively.
The untagged traffic goes to S2 and S5 and tagged to S1, S3, S4 and
S6. On the tagged sub-ports, the tags will be stripped and packets
will be sent to the respective Neutron networks.

On the way back, the reverse would be applied and each sub-port to VLAN
mapping be checked using something like following and packets will be
tagged:

+------+----------------------+---------------+
| Port | Tagged(VID)/untagged | Packets go to |
+======+======================+===============+
| S1   |                  100 | N1            |
+------+----------------------+---------------+
| S2   |             untagged | N3            |
+------+----------------------+---------------+
| S3   |                  200 | N1            |
+------+----------------------+---------------+
| S4   |                  100 | N2            |
+------+----------------------+---------------+
| S5   |             untagged | N4            |
+------+----------------------+---------------+
| S6   |                  300 | N2            |
+------+----------------------+---------------+


One thing to note over here is S1.vlan == S4.vlan is a valid scenario
since they are part of different trunk ports. It is possible that some
implementations do not use VLAN IDs, the VID can be something
other than VLAN ID. The fields in the sub-port can be treated as key
value pairs and corresponding support can be extended in the Kuryr agent
if there is a need.

Example of commands:

::

  magnum baymodel-create --name <name> \
                         --image-id <image> \
                         --keypair-id <kp>  \
                         --external-network-id <net-id> \
                         --dns-nameserver <dns> \
                         --flavor-id <flavor-id> \
                         --docker-volume-size <vol-size> \
                         --coe <coe-type> \
                         --network-driver kuryr

::

  neutron port-create --name S1 N1 \
                      --device-owner kuryr

::

  neutron port-create --name S2 N3


::

    # trunk-create may refer to 0, 1 or more subport(s).
    $ neutron trunk-create --port-id PORT \
                          [--subport PORT[,SEGMENTATION-TYPE,SEGMENTATION-ID]] \
                          [--subport ...]

Note: All ports referred must exist.

::

    # trunk-add-subport adds 1 or more subport(s)
    $ neutron trunk-subport-add TRUNK \
                                PORT[,SEGMENTATION-TYPE,SEGMENTATION-ID] \
                                [PORT,...]

::

  magnum container-create --name <name> \
                          --image <image> \
                          --bay <bay> \
                          --command <command> \
                          --memory <memory> \
                          --network network_id


Magnum changes
--------------

Magnum will launch containers on Neutron networks.
Magnum will provision the Kuryr Agent inside the Nova instances via Heat templates.


Alternatives
------------

None


Data Model Impact (Magnum)
--------------------------

This document adds the network_id attribute to the container database
table. A migration script will be provided to support the attribute
being added.

+-------------------+-----------------+---------------------------------------------+
|    Attribute      |     Type        |             Description                     |
+===================+=================+=============================================+
|     network_id    |     uuid        |    UUID of a Neutron network                |
+-------------------+-----------------+---------------------------------------------+


REST API Impact (Magnum)
-------------------------

This document adds network_id attribute to the Container
API class.

+-------------------+-----------------+---------------------------------------------+
|    Attribute      |     Type        |             Description                     |
+===================+=================+=============================================+
|     network_id    |     uuid        |     UUID of a Neutron network               |
+-------------------+-----------------+---------------------------------------------+


Security Impact
---------------

Kuryr Agent running inside Nova instances will communicate with OpenStack APIs. For this to
happen, credentials will have to be stored inside Nova instances hosting Bays.

This arrangement poses a security threat that credentials might be compromised and there
could be ways malicious containers could get access to credentials or Kuryr Agent.
To mitigate the impact, there are multiple options:

1. Run Kuryr Agent in two modes: primary and secondary. Only primary mode has access to the
   credentials and talks to Neutron and fetches information about available resources
   like IPs, VLANs. Secondary mode has no information about credentials and performs operations
   based on information coming in the input like IP, VLAN etc. Primary mode can be tied to the
   Kubernetes, Mesos master nodes. In this option, containers will be running on nodes other
   than the ones that talk to OpenStack APIs.
2. Containerize the Kuryr Agent to offer isolation from other containers.
3. Instead of storing credentials in text files, use some sort of binaries
   and make them part of the container running Kuryr Agent.
4. Have an Admin provisioned Nova instance that carries the credentials
   and has connectivity to the tenant Bays. The credentials are accessible only to the Kuryr
   agent via certain port that is allowed through security group rules and secret key.
   In this option, operations like VM snapshot in tenant domains will not lead to stolen credentials.
5. Introduce Keystone authentication mechanism for Kuryr Agent. In case of a compromise, this option
   will limit the damage to the scope of permissions/roles the Kuryr Agent will have.
6. Use HTTPS for communication with OpenStack APIs.
7. Introduce a mechanism/tool to detect if a host is compromised and take action to stop any further
   damage.

Notifications Impact
--------------------

None

Other End User Impact
---------------------

None

Performance Impact
------------------

For containers inside the same VM to communicate with each other,
the packets will have to step outside the VMs and come back in.


IPv6 Impact
-----------

None

Other Deployer Impact
---------------------

None

Developer Impact
----------------

Extended attributes in Magnum container API to be used.

Introduction of Kuryr Agent.

Requires the testing framework changes.


Community Impact
----------------

The changes bring significant improvement in the container
networking approach by using Neutron as a backend via Kuryr.


Implementation
==============

Assignee(s)
-----------

 Fawad Khaliq (fawadkhaliq)
 Vikas Choudhary (vikasc)

Work Items
----------

Magnum:

* Extend the Magnum API to support new network attribute.
* Extend the Client API to support new network attribute.
* Extend baymodel objects to support new container
  attributes. Provide a database migration script for
  adding the attribute.
* Extend unit and functional tests to support new port attribute
  in Magnum.

Heat:

* Update Heat templates to support the Magnum container
  port information.

Kuryr:

* Kuryr container agent.
* Kuryr VLAN/VID allocation engine.
* Extend unit test cases in Kuryr for the agent and VLAN/VID allocation
  engine.
* Other tempest tests.
* Other scenario tests.


Dependencies
============

VLAN aware VMs [2] implementation in Neutron


Testing
=======

Tempest and functional tests will be created.


Documentation Impact
====================

Documentation will have to updated to take care of the
Magnum container API changes and use the Kuryr network
driver.

User Documentation
------------------

Magnum and Kuryr user guides will be updated.

Developer Documentation
-----------------------

The Magnum and Kuryr developer quickstart documents will be
updated to include the nested container use case and the
corresponding details.


References
==========

[1] https://review.openstack.org/#/c/204686/7

[2] http://specs.openstack.org/openstack/neutron-specs/specs/mitaka/vlan-aware-vms.html

[3] https://blueprints.launchpad.net/kuryr/+spec/kuryr-agent

[4] https://blueprints.launchpad.net/kuryr/+spec/kuryr-magnum-heat-deployment

[5] http://docs.openstack.org/developer/magnum/
