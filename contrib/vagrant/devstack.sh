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

  # copy localrc settings (source: devstack/samples/localrc)
  echo "copy config from $BASHPATH/config/localrc to $DEVSTACK/localrc"
  cp "$BASHPATH"/config/localrc "$DEVSTACK"/localrc
  chown "$OS_USER":"$OS_USER" "$DEVSTACK"/localrc

fi


# start devstack
echo "Start Devstack"
su "$OS_USER" -c "cd $DEVSTACK && ./stack.sh"
