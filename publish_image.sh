#!/bin/bash

# publish code borrowed from publish_docs script

set -e
[ -n "$DEBUG" ] && set -x

. ./role_configrc

trap "rm -f /tmp/swift_description-*" EXIT

function publish {
    SRC=$1
    IMG=$(basename $SRC)
    IMG_NAME=$2
    cd $(dirname $SRC)
    echo "[+] Check if $IMG have changed"
    TMP_FILE=$(mktemp /tmp/swift_description-${IMG_NAME}-XXXXXX)
    curl -o ${TMP_FILE} ${SWIFT_SF_URL}/${IMG_NAME}.description
    diff ${TMP_FILE} ${IMG_NAME}.description 2> /dev/null && return
    rm -f ${TMP_FILE}
    echo "[+] Upstream is out dated"
    if [ ! -f "${IMG_NAME}.tgz" ]; then
        rm -f "${IMG_NAME}.tgz"
    fi
    echo "[+] Creating edeploy file of ${SRC}"
    (cd $IMG; sudo tar -c -p --use-compress-program=pigz --numeric-owner --xattrs --selinux -f ../${IMG_NAME}.tgz .)
    if [ "${IMG_NAME}" != "sf-centos7" ]; then
        for arch in $(ls ${ORIG}/config/refarch/*.yaml); do
            (cd ${ORIG}/deploy/heat; sudo ./deploy.py --arch ${arch} --output ${SRC}-${SF_VER}-$(basename $arch .yaml).hot render)
        done
    fi
    echo "[+] Creating manifest"
    OBJ="$(/bin/ls ${IMG_NAME}.{tgz,description,img.qcow2} ${IMG_NAME}-allinone.hot ${IMG_NAME}-allinone-fixed-ip.hot 2> /dev/null || true)"
    sha256sum $OBJ | sudo tee ${IMG_NAME}.digest
    for OBJECT in $OBJ ${IMG_NAME}.digest ${IMG_NAME}*.hot; do
        [ -f ${OBJECT} ] || continue
        echo "[+] Uploading ${OBJECT} to ${SWIFT_BASE_URL}/v1/AUTH_${SWIFT_ACCOUNT}/${SWIFT_IMAGE_CONTAINER}/"
        SWIFT_PATH="/v1/AUTH_${SWIFT_ACCOUNT}/${SWIFT_IMAGE_CONTAINER}/${OBJECT}"
        set +x
        TEMPURL=`swift tempurl PUT 120 ${SWIFT_PATH} ${TEMP_URL_KEY}`
        set -x
        curl -f -i -X PUT --upload-file "$OBJECT" "${SWIFT_BASE_URL}${TEMPURL}"
    done
}

ORIG=$(pwd)
echo "=== Publish image ${IMAGE_PATH} ==="
publish ${IMAGE_PATH} softwarefactory-${SF_VER}
echo "=== Publish cache ${CACHE_PATH} ==="
publish ${CACHE_PATH} sf-centos7
