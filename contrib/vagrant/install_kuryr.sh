#!/bin/sh

echo "running apt-get install python-pip"
sudo apt-get install -qqy python-pip
echo "running git clone kuryr"

su "$OS_USER" -c "cd ~ && git clone -b master https://github.com/openstack/kuryr"
su "$OS_USER" -c "cd ~/kuryr && sudo pip install -r requirements.txt"


