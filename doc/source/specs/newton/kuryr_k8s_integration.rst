..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

============================
Kuryr Kubernetes Integration
============================

https://blueprints.launchpad.net/kuryr/+spec/kuryr-k8s-integration

This spec proposes how to integrate Kubernetes Bare Metal cluster with Neutron
being used as network provider.

Kubernetes is a platform for automating deployment, scaling and operations of
application containers across clusters of hosts. There are already a number of
implementations of kubernetes network model, such as Flannel, Weave, Linux
Bridge, OpenvSwitch, Calico as well as other vendor implementations. Neutron
already serves as a common way to support various networking providers via
common API. Therefore, using neutron to provide kubernetes networking will
enable different backend support in a common way.

This approach provides clear benefit for operators who will have variety of
networking choices that already supported via neutron.


Problem Description
===================
Application developers usually are not networking engineers. They should be
able to express the application intent. Currently, there is no integration
between kubernetes and Neutron. Kuryr should bridge the gap between kubernetes
and neutron by using the application intent to infer the connectivity and
isolation requirements necessary to provision the networking entities in a
consistent way.

Kubernetes Overview
-------------------

Kubernetes API abstractions:

**Namespace**
  Serves as logical grouping of partition resources. Names of resources need to
  be unique within a namespace, but not across namespaces.

**Pod**
  Contains a group of tightly coupled containers that share single network
  namespace. Pod models an application-specific "logical host" in a
  containerized environment. It may contain one or more containers which are
  relatively tightly coupled. Each pod gets its own IP that is also an IP of
  the contained Containers.

**Deployment/Replication Controller**
  Ensures the requested number of pods are running at any time.

**Service**
  Is an abstraction which defines a logical set of pods and a policy by which
  to access them. The set of service endpoints, usually pods that implement a
  given service is defined by the label selector. The default service type
  (ClusterIP) is used to provide consistent application inside the kubernetes
  cluster. Service receives a service portal (VIP and port). Service IPs are
  only  available inside the cluster.
  Service can abstract access not only to pods. For example, it can be for
  external database  cluster, service in another namespace, etc. In such case
  service does not have a selector and endpoint are defined as part of the
  service. The service can be headless (clusterIP=None). For such Services,
  a cluster IP is not allocated. DNS should  return multiple addresses for the
  Service name, which point directly to the Pods  backing the Service.
  To receive traffic from the outside, service should be assigned an external
  IP address.
  For more details on service, please refer to [1]_.

Kubernetes provides two options for service discovery, environments variables
and DNS. Environment variables are added for each active service when pod is
run on the node. DNS is kubernetes cluster add-on that provides DNS server,
more details on this below.

Kubernetes has two more powerful tools, labels and annotations. Both can be
attached to the API objects. Labels are an arbitrary key/value pairs. Labels
do not provide uniqueness. Labels are queryable and used to organize and to
select subsets of objects.

Annotations are string keys and values that can be used by external tooling to
store arbitrary metadata.

More detailed information on k8s API can be found in [2]_


Network Requirements
^^^^^^^^^^^^^^^^^^^^
k8s imposes some fundamental requirements on the networking implementation:

* All containers can communicate without NAT.

* All nodes can communicate with containers without NAT.

* The IP the containers sees itself is the same IP that others see.

The kubernetes model is for each pod to have an IP in a flat shared namespace
that allows full communication with physical computers and containers across
the network. The above approach makes it easier than native Docker model to
port applications from VMs to containers. More on kubernetes network model
is here [3]_.


Use Cases
---------
The kubernetes networking should address requirements of several stakeholders:

* Application developer, the one that runs its application on the k8s cluster

* Cluster administrator, the one that runs the k8s cluster

* Network infrastructure administrator, the one that provides the physical
  network

Use Case 1:
^^^^^^^^^^^
Support current kubernetes network requirements that address application
connectivity needs. This will enable default kubernetes behavior to allow all
traffic from all sources inside or outside the cluster to all pods within the
cluster. This use case does not add multi-tenancy support.

Use Case 2:
^^^^^^^^^^^
Application isolation policy support.
This use case is about application isolation policy support as it is defined
by kubernetes community, based on spec [4]_. Network isolation policy will
impose limitations on the connectivity from an optional set of traffic sources
to an optional set of destination TCP/UDP ports.
Regardless of network policy, pods should be accessible by the host on which
they are running to allow local health checks. This use case does not address
multi-tenancy.

More enhanced use cases can be added in the future, that will allow to add
extra functionality that is supported by neutron.


Proposed Change
===============


Model Mapping
-------------

In order to support kubernetes networking via neutron, we should define how
k8s model maps into neutron model.
With regards to the first use case, to support default kubernetes networking
mode, the mapping can be done in the following way:

+-----------------+-------------------+---------------------------------------+
| **k8s entity**  | **neutron entity**| **notes**                             |
+=================+===================+=======================================+
|namespace        | network           |                                       |
+-----------------+-------------------+---------------------------------------+
|cluster subnet   | subnet pool       | subnet pool for subnets to allocate   |
|                 |                   | Pod IPs. Current k8s deployment on    |
|                 |                   | GCE uses subnet per node to leverage  |
|                 |                   | advanced routing. This allocation     |
|                 |                   | scheme should be supported as well    |
+-----------------+-------------------+---------------------------------------+
|service cluster  | subnet            | VIP subnet, service VIP will be       |
|ip range         |                   | allocated from                        |
+-----------------+-------------------+---------------------------------------+
|external subnet  | floating ip pool  | To allow  external access to services,|
|                 | external network  | each service should be assigned with  |
|                 | router            | external (floating IP) router is      |
|                 |                   | required to enable north-south traffic|
+-----------------+-------------------+---------------------------------------+
|pod              | port              | A port gets its IP address from the   |
|                 |                   | cluster subnet pool                   |
+-----------------+-------------------+---------------------------------------+
|service          | load balancer     | each endpoint (pod) is a member in the|
|                 |                   | load balancer pool. VIP is allocated  |
|                 |                   | from the service cluster ip range.    |
+-----------------+-------------------+---------------------------------------+

k8s Service Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^
Kubernetes default **ClusterIP** service type is used to expose service inside
the cluster. If users decide to expose services to external traffic, they will
assign ExternalIP to the services they choose to expose. Kube-proxy should be
an optional part of the deployment, since it may not work with some  neutron
backend solutions, i.e. MidoNet or Contrail. Kubernetes service will be mapped
to the neutron Load Balancer, with ClusterIP as the load balancer VIP and
EndPoints (Pods) are members of the load balancer.
Once External IP is assigned, it will create FIP on external network and
associate it with the VIP.


Isolation Policy
^^^^^^^^^^^^^^^^
In order to support second use case, the application isolation policy mode,
requested policy should be translated into security group that reflects the
requested ACLs as the group rules. This security group will be associated with
pods that policy is applied to. Kubernetes namespace can be used as isolation
scope of the contained Pods. For isolated namespace, all incoming connections
to pods in that namespace from any source inside or outside of the Kubernetes
cluster will be denied unless allowed by a policy.
For non-isolated namespace, all incoming connections to pods in that namespace
will be allowed.
The exact translation details are provided in the [5]_.

As an alternative, and this goes beyond neutron, it seems that more native way
might be to use policy (intent) based API to request the isolation policy.
Group Based Policy can be considered, but this will be left for the later phase.

Service Discovery
-----------------
Service discovery should be supported via environment variables.
Kubernetes also offers a DNS cluster add-on to support application services name
resolution. It uses SkyDNS with helper container, kube2sky to bridge between
kubernetes to SkyDNS and etcd to maintain services registry.
Kubernetes Service DNS names can be resolved using standard methods inside the
pods (i.e. gethostbyname). DNS server runs as kubernetes service with assigned
static IP from the service cluster ip range. Both DNS server IP and domain are
configured and passed to the kubelet service on each worker node that passes it
to containers. SkyDNS service is deployed in the kube-system namespace.
This integration should enable SkyDNS support as well as it  may add support
for external DNS servers. Since SkyDNS service will be deployed as any other
k8s service, this should just work.
Other alternatives for DNS, such as integration with OpenStack Designate for
local DNS  resolution by port name will be considered for later phases.


Integration Decomposition
-------------------------

The user interacts with the system via the kubectl cli or directly via REST API
calls. Those calls define Kubernetes resources such as RC, Pods and services.
The scheduler sees the requests for Pods and assigns them to a specific worker
nodes.

On the worker nodes, kubelet daemons see the pods that are being scheduled for
the node and take care of creating the Pods, i.e. deploying the infrastructure
and application containers and ensuring the required connectivity.

There are two conceptual parts that kuryr needs to support:

API Watcher
^^^^^^^^^^^
To watch kubernetes API server for changes in services and pods and later
policies collections.
Upon changes, it should map services/pods into the neutron constructs,
ensuring connectivity. It should use neutron client to invoke neutron API to
maintain networks, ports, load balancers, router interfaces and security groups.
The API Watcher will add allocated port details to the Pod object to make it
available to the kubelet process and eventually to the kuryr CNI driver.

CNI Driver
^^^^^^^^^^
To enable CNI plugin on each worker node to setup, teardown and provide status
of the Pod, more accurately of the infrastructure container. Kuryr will provide
CNI Driver that implements [6]_. In order to be able to configure and report an
IP configuration, the Kuryr CNI driver must be able to access IPAM to get IP
details for the Pod. The IP, port UUID, GW and port type details should be
available to the driver via **CNI_ARGS** in addition to the standard content::

   CNI_ARGS=K8S_POD_NAMESPACE=default;\
   K8S_POD_NAME=nginx-app-722l8;\
   K8S_POD_INFRA_CONTAINER_ID=8ceb00926acf251b34d70065a6158370953ab909b0745f5f4647ee6b9ec5c250\
   PORT_UUID=a28c7404-7495-4557-b7fc-3e293508dbc6,\
   IPV4=10.0.0.15/16,\
   GW=10.0.0.1,\
   PORT_TYPE=midonet

For more details on kuryr CNI Driver, see [7]_.

Kube-proxy service that runs on each worker node and implements the service in
native implementation is not required since service is implemented via neutron
load balancer.


Community Impact
----------------

This spec invites community to collaborate on unified solution to support
kubernetes networking by using neutron as a backend via Kuryr.


Implementation
==============

Assignee(s)
-----------

TBD

Work Items
----------

TBD


References
==========
.. [1] http://kubernetes.io/v1.1/docs/user-guide/services.html
.. [2] http://kubernetes.io/docs/api/
.. [3] http://kubernetes.io/docs/admin/networking/#kubernetes-model
.. [4] https://docs.google.com/document/d/1qAm-_oSap-f1d6a-xRTj6xaH1sYQBfK36VyjB5XOZug
.. [5] https://review.openstack.org/#/c/290172/
.. [6] https://github.com/appc/cni/blob/master/SPEC.md
.. [7] https://blueprints.launchpad.net/kuryr/+spec/kuryr-cni-plugin
