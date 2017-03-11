#!/bin/bash
# This script re-use a software-factory image as a nodepool slave

sudo rm /etc/yum.repos.d/jenkins.repo
sudo userdel jenkins

# Set tests domain name to the nodepool client ip
echo $(echo $SSH_CONNECTION | awk '{ print $1 }' ) sftests.com | sudo tee -a /etc/hosts
cat /etc/hosts

[ -d /etc/software-factory ] || mkdir /etc/software-factory
touch /etc/software-factory/health-check-nodepool-slave

# Set dns until nested rdo dhcp dns resolver is fixed
echo nameserver 8.8.8.8 > /etc/resolv.conf
cat /etc/resolv.conf

. base.sh
