vagrant-devstack-Kuryr
======================

Getting started
---------------

A Vagrant based kuryr,neutron,keystone and experimental docker system.

Steps to try vagrant image:

 1. Install Vagrant on your local machine. Install one of the current
    providers supported: VirtualBox, Libvirt or Vagrant
 2. Git clone Kuryr repository.
 3. Run `cd kuryr/contrib/vagrant`
 4. Run `vagrant up`
    It will take around 10 mins.
 5. `vagrant ssh`
    You will get vm shell with keystone and neutron already running.
 6. Run `cd kuryr && ./scripts/run_kuryr.sh &`
    Kuryr service will be up and listening on port 2377.
 7. Create the default Kuryr subnetpool:

        neutron subnetpool-create --default-prefixlen 24 --pool-prefix 10.10.0.0/16 kuryr

At this point you should have experimental docker, kuryr, neutron, keystone all
up, running and pointing to each other. Any docker network related commands can
be tried now as explained in [1].

References:

[1] https://github.com/openstack/kuryr/blob/master/doc/source/devref/libnetwork\_remote\_driver\_design.rst#L64

Vagrant Options available
-------------------------

You can set the following environment variables before running `vagrant up` to modify
the definition of the Virtual Machine spawned:

 * **VAGRANT\_KURYR\_VM\_BOX**: To change the Vagrant Box used. Should be available in
   [atlas](atlas.hashicorp.com).

       export VAGRANT_KURYR_VM_BOX=centos/7

   Could be an example of a rpm-based option.

 * **VAGRANT\_KURYR\_VM\_MEMORY**: To modify the RAM of the VM. Defaulted to: 4096
 * **VAGRANT\_KURYR\_VM\_CPU**: To modify the cpus of the VM. Defaulted to: 2
