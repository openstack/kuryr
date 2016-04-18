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
    You will get a VM with everything running.
    You will get vm shell with keystone and neutron already running.

At this point you should have experimental docker, kuryr, neutron, keystone all
up, running and pointing to each other. Any docker network related commands can
be tried now as explained in [1].

References:

[1] https://github.com/openstack/kuryr/blob/master/doc/source/devref/libnetwork_remote_driver_design.rst#L64

Vagrant Options available
-------------------------

You can set the following environment variables before running `vagrant up` to modify
the definition of the Virtual Machine spawned:

 * **VAGRANT\_KURYR\_VM\_BOX**: To change the Vagrant Box used. Should be available in
   [atlas](http://atlas.hashicorp.com).

       export VAGRANT_KURYR_VM_BOX=centos/7

   Could be an example of a rpm-based option.

 * **VAGRANT\_KURYR\_VM\_MEMORY**: To modify the RAM of the VM. Defaulted to: 4096
 * **VAGRANT\_KURYR\_VM\_CPU**: To modify the cpus of the VM. Defaulted to: 2
 * **VAGRANT\_KURYR\_RUN\_DEVSTACK**: Whether `vagrant up` should run devstack to
   have an environment ready to use. Set it to 'false' if you want to edit
   `local.conf` before run ./stack.sh manually in the VM. Defaulted to: true.
   See below for additional options for editing local.conf.

Additional devstack configuration
---------------------------------

To add additional configuration to local.conf before the VM is provisioned, you can
create a file called "user_local.conf" in the contrib/vagrant directory of
networking-kuryr. This file will be appended to the "local.conf" created during the
Vagrant provisioning.

For example, to use OVN as the Neutron plugin with Kuryr, you can create a
"user_local.conf" with the following configuration:

    enable_plugin networking-ovn http://git.openstack.org/openstack/networking-ovn
    enable_service ovn-northd
    enable_service ovn-controller
    disable_service q-agt
    disable_service q-l3
