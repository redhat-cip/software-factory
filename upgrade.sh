#!/bin/bash

source role_configrc

# Version must be passed as argument here
wanted=$1

# get the domain from sfconfig.yaml
DOMAIN=$(egrep "^domain:" /etc/puppet/hiera/sf/sfconfig.yaml | sed 's/domain://' | tr -d ' ')

# Clone Software-Factory and jump in the right tag
clone_path=/srv/software-factory
if [ ! -d "$clone_path" ]; then
    git clone http://softwarefactory.enovance.com/r/software-factory $clone_path
    cd $clone_path
    git checkout $wanted
fi

# We should make so verification
# Are we able to upgrade the JJB and Zuul provided conf
echo

# Start the upgrade by jumping in the cloned version
cd /srv/software-factory/upgrade/${PREVIOUS_SF_VER}/${SF_VER}/
cp group_vars/all.tmpl group_vars/all
sed -i "s/FROM/${PREVIOUS_SF_VER}/" group_vars/all
sed -i "s/TO/${SF_VER}/" group_vars/all
sed -i "s/DOMAIN/${DOMAIN}/" group_vars/all
ansible-playbook -i hosts site.yml
