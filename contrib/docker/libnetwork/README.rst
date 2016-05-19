=================================
Kuryr Docker libnetwork container
=================================

This is the container generation file for Kuryr's Docker libnetwork driver,
useful for single Docker engine usage as well as Docker Swarm usage.

How to build the container
--------------------------

If you want to build your own container, you can just build it by running the
following command from this same directory:

::

    docker build -t your_docker_username/libnetwork:latest .

How to get the container
------------------------

To get the upstream docker libnetwork container with ovs, you can just do:

::

    docker pull kuryr/libnetwork:latest

It is expected that different vendors may have their own versions of the
Kuryr libnetwork container in their docker hub namespaces, for example:

::

    docker pull midonet/libnetwork:latest

The reason for this is that some vendors' binding scripts need different (and
potentially non-redistributable) userspace tools in the container.

How to run the container
------------------------

First we prepare Docker to find the driver

::

    sudo mkdir -p /usr/lib/docker/plugins/kuryr
    sudo curl -o /usr/lib/docker/plugins/kuryr/kuryr.spec \
    https://raw.githubusercontent.com/openstack/kuryr/master/etc/kuryr.spec
    sudo service docker restart

Then we start the container

::

    docker run --name kuryr-libnetwork \
      --net=host \
      --cap-add=NET_ADMIN \
      -e SERVICE_USER=admin \
      -e SERVICE_TENANT_NAME=admin \
      -e SERVICE_PASSWORD=admin \
      -e IDENTITY_URL=http://127.0.0.1:35357/v2.0 \
      -e OS_URL=http://127.0.0.1:9696 \
      -v /var/log/kuryr:/var/log/kuryr \
      -v /var/run/openvswitch:/var/run/openvswitch \
      kuryr/libnetwork

Where:
* SERVICE_USER, SERVICE_TENANT_SERVICE_PASSWORD are OpenStack credentials
* IDENTITY_URL is the url to OpenStack Keystone
* OS_URL is the url to OpenStack Neutron
* k8S_API is the url to the Kubernetes API server
* A volume is created so that the logs are available on the host
* NET_ADMIN capabilities are given in order to perform network operations on
the host namespace like ovs-vsctl

Other options:
* CAPABILITY_SCOPE can be "local" or "global", the latter being for when there
is a cluster store plugged into the docker engine.
* LOG_LEVEL for defining, for example, "DEBUG" logging messages.
* PROCESSES for defining how many kuryr processes to use to handle the
libnetwork requests.
* THREADS for defining how many threads per process to use to handle the
libnetwork requests.

Note that the 127.0.0.1 are most likely to have to be changed unless you are
running everything on a single machine with `--net=host`.
