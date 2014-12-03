#!/bin/bash

# We should make so verification
# Are we able to upgrade the JJB and Zuul provided conf
echo

# Start the upgrade
source role_configrc
cd /srv/software-factory/upgrade/${PREVIOUS_SF_VER}/${SF_VER}/
ansible-playbook -i hosts site.yml
