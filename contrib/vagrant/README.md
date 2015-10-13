vagrant-devstack-Kuryr
=======================

A Vagrant based kuryr,neutron,keystone and experimental docker system.
Steps to try vagrant image:
1. Intall virtual-box and vagrant on your local machine.
2. Git clone kuryr repository.
3. cd kuryr/contrib/vagrant
4. vagrant up
   It will take around 10 mins.
5. vagrant ssh
   You will get vm shell with keystone and neutron already running.
6. cd kuryr && ./scripts/run_kuryr.sh &
   Kuryr service will be up and listening on port 2377.

At this point you should have experimental docker, kuryr, neutron, keystone
all up, running and pointing to each other. Any docker network related commands
can be tried now as explained in [1].

References:
[1] https://github.com/openstack/kuryr/blob/master/doc/source/devref/libnetwork_remote_driver_design.rst#L64


