#!/bin/bash

set -xe

function install_with_pip {
    package=$1
    dir=$(echo ${package}|sed -r 's/([a-zA-Z_-]+).*/\1/')
    sudo yum install -y python-virtualenv

    sudo virtualenv --system-site-packages --python=/usr/bin/python2 /opt/${dir}/venv
    sudo /opt/${dir}/venv/bin/pip install --install-option="--install-scripts=/usr/bin" ${package}
}


sudo yum update -y > /dev/null

# Base requirements
sudo yum install -y epel-release > /dev/null
sudo yum install -y python-pip git wget curl patch iproute > /dev/null

install_with_pip 'pip<8'
install_with_pip tox

# The jenkins user. Must be able to use sudo without password
sudo useradd -m jenkins
sudo gpasswd -a jenkins wheel
echo "jenkins ALL=(ALL) NOPASSWD:ALL" | sudo tee --append /etc/sudoers.d/90-cloud-init-users
echo "Defaults   !requiretty" | sudo tee --append /etc/sudoers.d/90-cloud-init-users

# SSH key for the Jenkins user
sudo mkdir /home/jenkins/.ssh
sudo cp /opt/nodepool-scripts/authorized_keys /home/jenkins/.ssh/authorized_keys
sudo ssh-keygen -N '' -f /home/jenkins/.ssh/id_rsa
sudo chown -R jenkins /home/jenkins/.ssh
sudo chmod 700 /home/jenkins/.ssh
sudo chmod 600 /home/jenkins/.ssh/authorized_keys
sudo restorecon -R -v /home/jenkins/.ssh/authorized_keys

# Nodepool will try to connect on the fresh node using the user
# defined as username in the provider.image section conf. Usually
# it is the clouduser. So fetch it and authorize the pub key
# for that user.
cloud_user=$(egrep " name:" /etc/cloud/cloud.cfg | awk '{print $2}')
cat /opt/nodepool-scripts/authorized_keys | sudo tee -a /home/$cloud_user/.ssh/authorized_keys

# Install java (required by Jenkins)
sudo yum install -y java

# Install glob2 and python-magic for zuul_swift_upload
sudo yum install -y python-magic
sudo pip install glob2

# Install zuul-cloner
# TODO: replace this section by zuul package
sudo yum install -y python-requests gcc python-devel python-crypto
install_with_pip zuul

# Copy slave tools
sudo cp -v /opt/nodepool-scripts/*.py /usr/local/bin/

# Install local CA
sudo cp /opt/nodepool-scripts/*.pem /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust

# sync FS, otherwise there are 0-byte sized files from the yum/pip installations
sudo sync
sudo sync

sudo cat /home/jenkins/.ssh/authorized_keys

echo "Base setup done."
