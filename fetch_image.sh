#!/bin/bash

# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

[ -z "$1" ] || SF_VER=$1
. ./role_configrc
[ -n "$DEBUG" ] && set -x

trap "rm -f /tmp/swift_hash-*" EXIT

function die {
    echo "[ERROR]: $1"
    exit -1
}

function fetch_prebuilt {
    echo "Fetch prebuilt ${IMG} ..."
    # Check if already synced
    if [ -f "${UPSTREAM}/${IMG}.hash" ]; then
        TMP_FILE=$(mktemp /tmp/swift_hash-${IMG}-XXXXXX)
        curl -o ${TMP_FILE} ${SWIFT_SF_URL}/${IMG}.hash
        # Swift does not return 404 but 'Not Found'
        grep -q 'Not Found' $TMP_FILE && die "$IMG does not exist upstream"
        diff ${TMP_FILE} ${UPSTREAM}/${IMG}.hash && {
            echo "Already synced"
            return
        }
    fi
    rm -f ${TMP_FILE}
    echo "Fetching ${SWIFT_SF_URL}/${IMG}.tgz"
    sudo curl -o ${UPSTREAM}/${IMG}.tgz ${SWIFT_SF_URL}/${IMG}.tgz || exit -1
    echo "Fetching ${SWIFT_SF_URL}/${IMG}.{pip,rpm,digest,hash}"
    sudo curl -o ${UPSTREAM}/${IMG}.pip ${SWIFT_SF_URL}/${IMG}.pip
    sudo curl -o ${UPSTREAM}/${IMG}.rpm ${SWIFT_SF_URL}/${IMG}.rpm
    sudo curl -o ${UPSTREAM}/${IMG}.digest ${SWIFT_SF_URL}/${IMG}.digest
    sudo curl -o ${UPSTREAM}/${IMG}.hash ${SWIFT_SF_URL}/${IMG}.hash || exit -1
    echo "Digests..."
    (cd ${UPSTREAM}; exec sha256sum -c ./${IMG}.digest) || exit -1
}

function sync_and_deflate {
    # DST is the path of system tree
    DST=$1
    # IMG is the name of image file
    IMG=$2
    fetch_prebuilt
    SRC=${UPSTREAM}/$2.tgz
    diff ${UPSTREAM}/${IMG}.hash ${DST}/../${IMG}.hash && {
        echo "already extracted"
        return
    }
    sudo rm -Rf ${DST}
    sudo mkdir -p ${DST}
    echo "[+] Extract image ${SRC} to ${DST}"
    sudo tar -xzf ${SRC} -C "${DST}" || exit -1
    echo "[+] Copy metadata"
    sudo cp ${UPSTREAM}/${IMG}.hash ${DST}/../${IMG}.hash
    sudo cp ${UPSTREAM}/${IMG}.pip ${DST}/../${IMG}.pip
    sudo cp ${UPSTREAM}/${IMG}.rpm ${DST}/../${IMG}.rpm
    sudo cp ${UPSTREAM}/${IMG}.digest ${DST}/../${IMG}.digest
}

prepare_buildenv

if [ -z "$FETCH_CACHE" ]; then
    sync_and_deflate ${IMAGE_PATH} "softwarefactory-${SF_VER}"
else
    sync_and_deflate ${CACHE_PATH} "sf-centos7"
fi
