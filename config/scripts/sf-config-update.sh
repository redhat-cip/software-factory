#!/bin/bash

cd /usr/local/share/sf-ansible
exec ansible-playbook sf_configrepo_update.yaml
