#!/bin/bash

# TODO: puppetize enocloud access
eval $(sudo cat /etc/sf-dom-enocloud.openrc)

set -e
set -x

. ./role_configrc

cd ${INST}
TEMP_DIR=$(mktemp -d /tmp/edeploy-check-XXXXX)
for role_name in install-server-vm mysql slave softwarefactory; do
    role=${role_name}-${SF_VER}
    echo "[+] Check if ${role} have changed"
    curl -s -o ${TEMP_DIR}/${role}.md5 ${BASE_URL}/${role}.md5 || true
    [ "$(cat ${TEMP_DIR}/${role}.md5)" == "$(cat ${role}.md5)" ] && continue
    echo "[+] Upstream is out dated, creating edeploy tarball"
    (cd ${role_name}; sudo tar czf ../${role}.edeploy *)
    md5sum ${role}.edeploy | sudo tee ${role}.edeploy.md5
done
rm -Rf ${TEMP_DIR}
swift upload --changed --verbose edeploy-roles *-${SF_VER}.*
