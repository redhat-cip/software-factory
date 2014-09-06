#!/bin/bash

# TODO: puppetize enocloud access
eval $(sudo cat /etc/sf-dom-enocloud.openrc)

set -e
set -x

. ./role_configrc

cd ${INST}
for role in install-server-vm mysql slave softwarefactory; do
    edeploy_name=${role}-${SF_REL}.edeploy
    sudo tar cjf ${edeploy_name} ${role}
    md5sum ${edeploy_name} | sudo tee ${edeploy_name}.md5
done
swift upload --changed --verbose edeploy-roles *-${SF_REL}.*

