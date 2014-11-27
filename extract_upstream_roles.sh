#!/bin/bash

. ./role_configrc

set -e

DEST_DIR="/var/lib/debootstrap/install/${SF_VER}"

[ -d "${DEST_DIR}" ] || mkdir ${DEST_DIR}

for role in install-server-vm softwarefactory; do
    SRC_FILE="${UPSTREAM}/${role}-${SF_VER}.edeploy"
    DST_TREE="${DEST_DIR}/${role}"
    [ -d ${DST_TREE} ] && rm -Rf ${DST_TREE}
    mkdir ${DST_TREE}
    echo "Extracting ${SRC_FILE} to ${DST_TREE}"
    tar -xzf ${SRC_FILE} -C ${DST_TREE}
done
touch ${DEST_DIR}.done
echo "Done."
