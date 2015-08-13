#!/bin/bash

. base.sh

# Prepare slave for SF
sudo sed -i 's/^.*SELINUX=.*$/SELINUX=disabled/' /etc/selinux/config
git clone http://softwarefactory.enovance.com/r/sfstack
cd sfstack && sudo ./sfinstall.sh
sudo mkdir /srv/deps
sudo chown -R jenkins /srv/
cd /srv/software-factory && ./fetch_roles.sh bases
cd /srv/software-factory && ./fetch_roles.sh trees
sudo chmod 777 /var/lib/sf/
ssh-keygen -N "" -f /home/jenkins/.ssh/id_rsa
sudo chown -R jenkins /home/jenkins/.ssh

# sync FS, otherwise there are 0-byte sized files from the yum/pip installations
sudo sync

echo "setup.sh finished. Creating snapshot now, this will take a few minutes"
