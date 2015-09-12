===============================
kuryr
===============================

Docker for Openstack Neutron

Kuryr is a Docker network plugin that uses Neutron to provide networking
services to Docker containers. It provides containerised images for the
common Neutron plugins.


* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/kuryr
* Source: http://git.openstack.org/cgit/openstack/kuryr
* Bugs: http://bugs.launchpad.net/kuryr

Features
--------

* TODO


Prerequisites
-------------

::

    $ sudo pip install -r requirements.txt

Running Kuryr
-------------

Please run the following script, it creates `/usr/lib/docker/plugins/kuryr`
and the JSON spec file, `/usr/lib/docker/plugins/kuryr/kuryr.json`, if they
don't exist.

::

    $ ./scripts/run_kuryr.sh

Testing Kuryr
-------------

::

    $ tox
