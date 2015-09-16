#!/bin/bash

# The jenkins user. Must be able to use sudo without password
sudo useradd -m jenkins
sudo gpasswd -a jenkins wheel
echo "jenkins ALL=(ALL) NOPASSWD:ALL" | sudo tee --append /etc/sudoers.d/90-cloud-init-users

# SSH key for the Jenkins user
sudo mkdir /home/jenkins/.ssh
sudo cp /opt/nodepool-scripts/authorized_keys /home/jenkins/.ssh/authorized_keys
sudo chown jenkins /home/jenkins/.ssh
sudo chown jenkins /home/jenkins/.ssh/authorized_keys
sudo chmod 700 /home/jenkins/.ssh
sudo chmod 600 /home/jenkins/.ssh/authorized_keys
sudo restorecon -R -v /home/jenkins/.ssh/authorized_keys

# Nodepool will try to connect on the fresh node using the user
# defined as username in the provider.image section conf. Usually
# it is the clouduser. So fetch it and authorize the pub key
# for that user.
cloud_user=$(egrep " name:" /etc/cloud/cloud.cfg | awk '{print $2}')
cat /opt/nodepool-scripts/authorized_keys | sudo tee -a /home/$cloud_user/.ssh/authorized_keys

# Required by Jenkins
sudo yum install -y java

# zuul-cloner is needed as well
sudo yum install -y epel-release
sudo yum install -y python-pip git python-devel gcc
sudo pip install zuul gitdb

# The Swarm client should be started by Jenkins via a request from Nodepool.
# If public_ip has been set in sfconfig.yaml then the slave can be aware
# of the Jenkins master IP via /etc/hosts.
echo "$NODEPOOL_SF_PUBLICIP $NODEPOOL_SF_TOPDOMAIN" | sudo tee --append /etc/hosts

# sync FS, otherwise there are 0-byte sized files from the yum/pip installations
sudo sync

echo "Base setup done."
