#!/bin/bash

set -e

BASHPATH=$(dirname "$0"\")
RUN_DEVSTACK="$1"
echo "Run script from $BASHPATH"

# Copied shamelessly from Devstack
function GetOSVersion {
  if [[ -x $(which lsb_release 2>/dev/null) ]]; then
    os_FAMILY='Debian'
  elif [[ -r /etc/redhat-release ]]; then
    os_FAMILY='RedHat'
  else
    echo "Unsupported distribution!"
    exit 1;
  fi
}

GetOSVersion

if [[ "$os_FAMILY" == "Debian" ]]; then
  export DEBIAN_FRONTEND noninteractive
  sudo apt-get update
  sudo apt-get install -qqy git
elif [[ "$os_FAMILY" == "RedHat" ]]; then
  sudo yum install -y -d 0 -e 0 git
fi

# determine checkout folder
PWD=$(su "$OS_USER" -c "cd && pwd")
DEVSTACK=$PWD/devstack

# check if devstack is already there
if [[ ! -d "$DEVSTACK" ]]
then
  echo "Download devstack into $DEVSTACK"

  # clone devstack
  su "$OS_USER" -c "cd && git clone -b master https://github.com/openstack-dev/devstack.git $DEVSTACK"

  echo "Copy configuration"

  # copy local.conf.sample settings (source: kuryr/devstack/local.conf.sample)
  cp /devstack/local.conf.sample $DEVSTACK/local.conf
  # If local settings are present, append them
  if [ -f "/vagrant/user_local.conf" ]; then
    cat /vagrant/user_local.conf >> $DEVSTACK/local.conf
  fi
  chown "$OS_USER":"$OS_USER" "$DEVSTACK"/local.conf

fi

if $RUN_DEVSTACK; then
  echo "Start Devstack"
  su "$OS_USER" -c "cd $DEVSTACK && ./stack.sh"
else
  echo "Virtual Machine ready. You can run devstack by executing '/home/vagrant/devstack/stack.sh'"
fi
