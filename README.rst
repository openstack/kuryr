===============================
kuryr
===============================

.. image:: https://raw.githubusercontent.com/openstack/kuryr/master/doc/images/kuryr_logo.png
    :alt: Kuryr
    :width: 67
    :height: 112
    :align: center


Docker for OpenStack Neutron

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

Please run the following script, it creates ``/usr/lib/docker/plugins/kuryr``
and the JSON spec file, ``/usr/lib/docker/plugins/kuryr/kuryr.json``, if they
don't exist. Kuryr requires the root privilege for creating and deleting the
veth pairs with `pyroute2 <http://docs.pyroute2.org/>`_ to run.

::

    $ sudo ./scripts/run_kuryr.sh

Testing Kuryr
-------------

::

    $ tox

You can also run specific test cases using the ``-e`` flag, e.g., to only run
the *fullstack* test case.

::

    $ tox -e fullstack

Generate Documentation
----------------------


We use `Sphinix <https://pypi.python.org/pypi/Sphinx>`_ to maintain the
documentation. You can install Sphinix using pip.

::

    $ pip install -U Sphinx

The source code of the documentation are under *doc*, you can generate the
html files using the following command. If the generation succeeds,a
*build/html* dir will be created under *doc*.

::

    $ cd doc
    $ make html

Now you can serve the documentation at http://localhost:8080 as a simple
website.

::

    $ cd build/html
    $ python -m SimpleHTTPServer 8080
