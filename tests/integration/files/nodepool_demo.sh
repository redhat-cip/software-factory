#!/bin/bash

sudo edeploy activate-pkgmngr
sudo userdel jenkins

# Set tests domain name to the nodepool client ip
echo $(echo $SSH_CONNECTION | awk '{ print $1 }' ) sftests.com | sudo tee -a /etc/hosts
cat /etc/hosts

# Set dns until nested rdo dhcp dns resolver is fixed
echo nameserver 8.8.8.8 > /etc/resolv.conf
cat /etc/resolv.conf

. base.sh
