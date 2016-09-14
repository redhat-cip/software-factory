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

trap "rm -f /tmp/swift_description-*" EXIT

function die {
    echo "[ERROR]: $1"
    exit -1
}

function fetch_prebuilt {
    echo "Fetch prebuilt ${IMG} to ${UPSTREAM}/${IMG}"
    # Check if already synced
    desc_ext="description"
    if [ "${SF_VER}" == "C7.0-2.0.4" ] || [ "${SF_VER}" == "C7.0-2.1.2" ]; then
        desc_ext="hash"
    fi
    if [ -f "${UPSTREAM}/${IMG}.${desc_ext}" ]; then
        TMP_FILE=$(mktemp /tmp/swift_description-${IMG}-XXXXXX)
        curl -o ${TMP_FILE} ${SWIFT_SF_URL}/${IMG}.${desc_ext}
        # Swift does not return 404 but 'Not Found'
        grep -q 'Not Found' $TMP_FILE && die "$IMG does not exist upstream"
        diff -up ${TMP_FILE} ${UPSTREAM}/${IMG}.${desc_ext} 2> /dev/null && {
            echo "Already synced"
            return
        }
    fi
    rm -f ${TMP_FILE}
    echo "Fetching ${SWIFT_SF_URL}/${IMG}.tgz"
    sudo curl -o ${UPSTREAM}/${IMG}.tgz ${SWIFT_SF_URL}/${IMG}.tgz
    echo "Fetching ${SWIFT_SF_URL}/${IMG}.img.qcow2"
    sudo curl -o ${UPSTREAM}/${IMG}.img.qcow2 ${SWIFT_SF_URL}/${IMG}.img.qcow2
    echo "Fetching ${SWIFT_SF_URL}/${IMG}.{digest,description,hot,hash}"
    # Fetch ${IMG}.hot for 2.1.8 digest
    sudo curl -o ${UPSTREAM}/${IMG}.hot ${SWIFT_SF_URL}/${IMG}.hot
    sudo curl -o ${UPSTREAM}/${IMG}-allinone.hot ${SWIFT_SF_URL}/${IMG}-allinone.hot
    sudo curl -o ${UPSTREAM}/${IMG}-allinone-fixed-ip.hot ${SWIFT_SF_URL}/${IMG}-allinone-fixed-ip.hot
    sudo curl -o ${UPSTREAM}/${IMG}.digest ${SWIFT_SF_URL}/${IMG}.digest
    sudo curl -o ${UPSTREAM}/${IMG}.description ${SWIFT_SF_URL}/${IMG}.description
    echo "Digests..."
    if [ -z "${SKIP_GPG}" ]; then
        gpg --list-sigs ${RELEASE_GPG_FINGERPRINT} &> /dev/null || gpg --keyserver keys.gnupg.net --recv-key ${RELEASE_GPG_FINGERPRINT}
        gpg --verify ${UPSTREAM}/${IMG}.digest || {
            echo "GPG check failed, to avoid error: export SKIP_GPG=1"
            exit -1
        }
    fi
    (cd ${UPSTREAM}; exec sha256sum -c ./${IMG}.digest) || exit -1
}

function sync_and_deflate {
    # DST is the path of system tree
    DST=$1
    # IMG is the name of image file
    IMG=$2
    fetch_prebuilt
    SRC=${UPSTREAM}/$2.tgz
    echo "Extracting ${SRC} to ${DST}"
    diff -up ${UPSTREAM}/${IMG}.description ${DST}/../${IMG}.description 2> /dev/null && {
        echo "Already extracted"
        return
    }
    sudo rm -Rf ${DST}
    sudo mkdir -p ${DST}
    sudo tar -x -p --use-compress-program=pigz --numeric-owner --xattrs --selinux -f ${SRC} -C "${DST}" || exit -1
    echo "[+] Copy metadata"
    sudo cp ${UPSTREAM}/${IMG}.description ${DST}/../${IMG}.description
    sudo cp ${UPSTREAM}/${IMG}.digest ${DST}/../${IMG}.digest
}

prepare_buildenv

if [ -z "$FETCH_CACHE" ]; then
    sync_and_deflate ${IMAGE_PATH} "softwarefactory-${SF_VER}"
else
    sync_and_deflate ${CACHE_PATH} "sf-centos7"
fi
