#!/bin/bash

# publish code borrowed from publish_docs script

set -e
set -x

. ./role_configrc

CONTAINER="edeploy-roles"

cd ${INST}
TEMP_DIR=$(mktemp -d /tmp/edeploy-check-XXXXX)
for role_name in softwarefactory; do
    role=${role_name}-${SF_VER}
    echo "[+] Check if ${role} have changed"
    curl -s -o ${TEMP_DIR}/${role}.md5 ${SWIFT_SF_URL}/${role}.md5 || true
    [ "$(cat ${TEMP_DIR}/${role}.md5)" == "$(cat ${role}.md5)" ] && continue
    echo "[+] Upstream is out dated, creating edeploy tarball"
    (cd ${role_name}; sudo tar czf ../${role}.edeploy *)
    md5sum ${role}.edeploy | sudo tee ${role}.edeploy.md5
    for OBJECT in ${role}.edeploy ${role}.edeploy.md5 ${role}.md5 ${role}.img.qcow2 ${role}.img.qcow2.md5 ${role}.rpm ${role}.pip; do
        SWIFT_PATH="/v1/AUTH_${SWIFT_ACCOUNT}/${CONTAINER}/${OBJECT}"
        set +x
        TEMPURL=`swift tempurl PUT 120 ${SWIFT_PATH} ${TEMP_URL_KEY}`
        set -x
        curl -f -i -X PUT --upload-file "$OBJECT" "${SWIFT_BASE_URL}${TEMPURL}" &> /dev/null && echo -n '.' || { echo 'Fail !'; exit 1; }
    done
done
rm -Rf ${TEMP_DIR}
