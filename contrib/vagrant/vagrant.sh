#!/bin/sh

export OS_USER=vagrant
export OS_HOST_IP=172.68.5.10

# run script
sh /vagrant/devstack.sh

# install experimetal docker
sh /vagrant/docker.sh

#install kuryr
sh /vagrant/install_kuryr.sh

#set environment variables for kuryr
su "$OS_USER" -c "echo 'source /vagrant/config/kuryr_rc' >> ~/.bashrc"

