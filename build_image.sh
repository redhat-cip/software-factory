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

LOCK="/var/run/sf-build_image.lock"
if [ -f ${LOCK} ]; then
    echo "Lock file present: ${LOCK}"
    killall softwarefactory.install
fi
sudo touch ${LOCK}
trap "sudo rm -f ${LOCK}" EXIT

set -e
[ -n "$DEBUG" ] && set -x

. ./role_configrc

if [ ! -z "${1}" ]; then
    ARTIFACTS_DIR=${1}/edeploy
    sudo mkdir -p ${ARTIFACTS_DIR}
    USER=$(whoami)
    sudo chown -R $USER:$USER ${ARTIFACTS_DIR}
fi


CURRENT=`pwd`
SF_ROLES=$CURRENT/edeploy/

function build_img {
    set -x
    ROLE_NAME="$1"
    ROLE_FILE="${INST}/${ROLE_NAME}-${SF_VER}.img"
    ROLE_TREE_PATH="${INST}/${ROLE_NAME}"
    CFG="$3"
    [ -f "$ROLE_FILE" ] && sudo rm -Rf $ROLE_FILE
    [ -f "${ROLE_FILE}.qcow2" ] && sudo rm -Rf "${ROLE_FILE}.qcow2"
    sudo $CREATE_IMG $ROLE_TREE_PATH $ROLE_FILE $CFG
    # Remove the raw image, only keep the qcow2 image
    sudo rm -f ${ROLE_FILE}
    sudo rm -f ${ROLE_FILE}.md5
    qcow2_md5=$(cat ${ROLE_FILE}.qcow2 | md5sum - | cut -d ' ' -f1)
    echo $qcow2_md5 | sudo tee ${ROLE_FILE}.qcow2.md5
}

function build_image {
    ROLE_NAME="$1"
    ROLE_MD5="$2"
    ROLE_FILE="${INST}/${ROLE_NAME}-${SF_VER}"

    echo "(STEP1) ${ROLE_NAME} local hash is ${ROLE_MD5}"

    if [ ! -f "${ROLE_FILE}.md5" ] || [ "$(cat ${ROLE_FILE}.md5)" != "${ROLE_MD5}" ]; then
        echo "(STEP1) The local cache for ${ROLE_NAME} md5 ($(cat ${ROLE_FILE}.md5)) is different to what we computed from your git branch state (${ROLE_MD5})."
        [ ! -d "${INST}/${ROLE_NAME}_cache" ] && sudo mkdir -p "${INST}/${ROLE_NAME}_cache"
        [ -z "$SKIP_BUILD" ] && {
            echo "(STEP1) Rebuilding cache now..."
            if [ ! -z "${ARTIFACTS_DIR}" ]; then
                ROLE_OUTPUT=${ARTIFACTS_DIR}/${ROLE_NAME}_step_1_build.log
            else
                ROLE_OUTPUT=/dev/stdout
            fi
            cd $SF_ROLES
            STEP=1 SDIR=/var/lib/sf/git/edeploy \
            sudo -E ./softwarefactory.install "${INST}/${ROLE_NAME}_cache" ${SF_VER} &> ${ROLE_OUTPUT} || { echo "(STEP1) Build failed"; sudo rm -Rf ${ROLE_FILE}.md5; exit 1; }
            cd -
        } || {
            echo "(STEP1) Skip rebuilding cache (forced)."
            return
        }
    fi
}

function finalize_image {
    ROLE_NAME="$1"
    ROLE_FILE="${INST}/${ROLE_NAME}-${SF_VER}"

    echo "(STEP2) Finalize image building..."

    # Make sure image tree is not mounted
    grep -q "${SF_VER}\/${ROLE_NAME}_cache\/proc" /proc/mounts && {
        while true; do
            sudo umount ${INST}/${ROLE_NAME}_cache/proc || break
        done
    }

    if [ ! -z "${ARTIFACTS_DIR}" ]; then
        ROLE_OUTPUT=${ARTIFACTS_DIR}/${ROLE_NAME}_step_2_build.log
    else
        ROLE_OUTPUT=/dev/stdout
    fi

    [ ! -d "${INST}/${ROLE_NAME}" ] && sudo mkdir -p "${INST}/${ROLE_NAME}"
    sudo rsync -a --delete "${INST}/${ROLE_NAME}_cache/" "${INST}/${ROLE_NAME}/"

    TAGGED_RELEASE=${TAGGED_RELEASE} PYSFLIB_PINNED_VERSION=${PYSFLIB_PINNED_VERSION} \
    MANAGESF_PINNED_VERSION=${MANAGESF_PINNED_VERSION} CAUTH_PINNED_VERSION=${CAUTH_PINNED_VERSION} \
    ./edeploy/fetch_subprojects.sh

    cd $SF_ROLES
    STEP=2 DOCDIR=$DOCDIR GERRITHOOKS=$GERRITHOOKS PYSFLIB_CLONED_PATH=$PYSFLIB_CLONED_PATH \
    CAUTH_CLONED_PATH=$CAUTH_CLONED_PATH MANAGESF_CLONED_PATH=$MANAGESF_CLONED_PATH \
    SDIR=/var/lib/sf/git/edeploy \
    sudo -E ./softwarefactory.install ${INST}/${ROLE_NAME} ${SF_VER} &> ${ROLE_OUTPUT}
    cd -

    echo ${ROLE_MD5} | sudo tee ${ROLE_FILE}.md5
}

prepare_buildenv
build_image "softwarefactory" $(find ${BASE_DEPS} -type f -not -path "*/.git/*" | sort | xargs cat | md5sum | awk '{ print $1}')
finalize_image "softwarefactory"
if [ -n "$VIRT" ]; then
    build_img "softwarefactory" $IMG_CFG
fi
