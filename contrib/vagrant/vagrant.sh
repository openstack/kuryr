#!/bin/sh

export OS_USER=vagrant
export OS_HOST_IP=172.68.5.10

# run script
bash /vagrant/devstack.sh

#set environment variables for kuryr
su "$OS_USER" -c "echo 'source /vagrant/config/kuryr_rc' >> ~/.bashrc"
