#!/bin/bash

# TODO: puppetize enocloud access
eval $(sudo cat /etc/sf-dom-enocloud.openrc)

set -e
set -x

. ./role_configrc

cd ${INST}
TEMP_DIR=$(mktemp -d /tmp/edeploy-check-XXXXX)
for role in install-server-vm mysql slave softwarefactory; do
    role=${role}-${SF_REL}
    # check if role have changed
    curl -s -o ${TEMP_DIR}/${role}.md5 ${BASE_URL}/${role}.md5 || true
    [ "$(cat ${TEMP_DIR}/${role}.md5)" == "$(cat ${role}.md5)" ] && continue
    edeploy_name=${role}-${SF_REL}.edeploy
    sudo tar cjf ${edeploy_name} ${role}
    md5sum ${edeploy_name} | sudo tee ${edeploy_name}.md5
done
rm -Rf ${TEMP_DIR}
swift upload --changed --verbose edeploy-roles *-${SF_REL}.*
