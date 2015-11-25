#!/bin/sh

BASHPATH=$(dirname "$0"\")
echo "run script from $BASHPATH"

# update system
export DEBIAN_FRONTEND noninteractive
sudo apt-get update
sudo apt-get install -qqy git

# determine checkout folder
PWD=$(su "$OS_USER" -c "cd && pwd")
DEVSTACK=$PWD/devstack

# check if devstack is already there
if [ ! -d "$DEVSTACK" ]
then
  echo "Download devstack into $DEVSTACK"

  # clone devstack
  su "$OS_USER" -c "cd && git clone -b master https://github.com/openstack-dev/devstack.git $DEVSTACK"

  echo "Copy configuration"

  # copy local.conf.sample settings (source: kuryr/devstack/local.conf.sample)
  cp /vagrant/devstack/local.conf.sample $DEVSTACK/local.conf
  chown "$OS_USER":"$OS_USER" "$DEVSTACK"/local.conf

fi

# start devstack
echo "Start Devstack"
su "$OS_USER" -c "cd $DEVSTACK && ./stack.sh"
