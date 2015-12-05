#!/bin/bash

. base.sh

# This should be removed after we fix functestlib.sh and how
# we manage to store artifacts
sudo useradd www-data

sudo yum install -y epel-release

sudo yum install -y git python-augeas bridge-utils curl lxc wget swig python-devel python-pip graphviz python-yaml openssl-devel libffi-devel pigz mysql-devel openldap-devel qemu-img libvirt-daemon-lxc git-review
sudo pip install flake8 bash8 ansible
sudo pip install -U tox==1.6.1 Sphinx oslosphinx virtualenv restructuredtext_lint python-swiftclient

sudo dd if=/dev/zero of=/srv/swap count=4000 bs=1M
sudo chmod 600 /srv/swap
sudo mkswap /srv/swap
grep swap /etc/fstab || echo "/srv/swap none swap sw 0 0" | sudo tee -a /etc/fstab

sudo sed -i 's/^.*SELINUX=.*$/SELINUX=disabled/' /etc/selinux/config

sudo mkdir -p /var/lib/sf
sudo mkdir -p /var/lib/sf/artifacts/logs
sudo chown -R jenkins:jenkins /var/lib/sf/

# Temporary DNS fix
echo "216.58.213.16 gerrit-releases.storage.googleapis.com" | sudo tee -a /etc/hosts

# Fetch prebuilt image
git clone http://softwarefactory-project.io/r/software-factory --depth 1
(
    cd software-factory;
    ./fetch_image.sh
    FETCH_CACHE=1 ./fetch_image.sh
)

# sync FS, otherwise there are 0-byte sized files from the yum/pip installations
sudo sync

echo "Setup finished. Creating snapshot now, this will take a few minutes"
