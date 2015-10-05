#!/bin/bash

# publish code borrowed from publish_docs script

set -e
[ -n "$DEBUG" ] && set -x

. ./role_configrc

CONTAINER="edeploy-roles"

trap "rm -f /tmp/swift_hash-*" EXIT

function publish {
    SRC=$1
    IMG=$(basename $SRC)
    IMG_NAME=$2
    cd $(dirname $SRC)
    echo "[+] Check if $IMG have changed"
    TMP_FILE=$(mktemp /tmp/swift_hash-${IMG_NAME}-XXXXXX)
    curl -o ${TMP_FILE} ${SWIFT_SF_URL}/${IMG_NAME}.hash
    diff ${TMP_FILE} ${IMG_NAME}.hash 2> /dev/null && return
    rm -f ${TMP_FILE}
    echo "[+] Upstream is out dated"
    if [ ! -f "${IMG_NAME}.tgz" ]; then
        echo "[+] Creating edeploy file of ${SRC}"
        (cd $IMG; sudo tar -c -p --use-compress-program=pigz -f ../${IMG_NAME}.tgz .)
    fi
    for hot in $(ls ${HOT_TEMPLATES}/*.hot); do
        sudo cp $hot $(basename $hot | sed "s/\.hot/-${SF_VER}.hot/")
    done
    echo "[+] Creating manifest"
    OBJ="$(/bin/ls ${IMG_NAME}.{tgz,hash,pip,rpm,img.qcow2,hot} 2> /dev/null || true)"
    sha256sum $OBJ | sudo tee ${IMG_NAME}.digest
    for OBJECT in $OBJ ${IMG_NAME}.digest; do
        [ -f ${OBJECT} ] || continue
        echo "[+] Uploading ${OBJECT} to ${SWIFT_BASE_URL}/v1/AUTH_${SWIFT_ACCOUNT}/${CONTAINER}/"
        SWIFT_PATH="/v1/AUTH_${SWIFT_ACCOUNT}/${CONTAINER}/${OBJECT}"
        set +x
        TEMPURL=`swift tempurl PUT 120 ${SWIFT_PATH} ${TEMP_URL_KEY}`
        set -x
        curl -f -i -X PUT --upload-file "$OBJECT" "${SWIFT_BASE_URL}${TEMPURL}"
    done
}

echo "=== Publish image ${IMAGE_PATH} ==="
publish ${IMAGE_PATH} softwarefactory-${SF_VER}
echo "=== Publish cache ${CACHE_PATH} ==="
publish ${CACHE_PATH} sf-centos7
