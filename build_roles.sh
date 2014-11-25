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
set -x

LOCK="/var/run/sf-build_roles.lock"
if [ -f ${LOCK} ]; then
    echo "Lock file present: ${LOCK}"
    killall make
fi
sudo touch ${LOCK}
trap "sudo rm -f ${LOCK}" 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15

set -e
[ -n "$DEBUG" ] && set -x

. ./role_configrc

CURRENT=`pwd`
SF_ROLES=$CURRENT/edeploy/

function build_img {
    ROLE_FILE="${1}.img"
    ROLE_TREE_PATH="$2"
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

function build_role {
    ROLE_NAME="$1"
    ROLE_MD5="$2"
    ROLE_FILE="${INST}/${ROLE_NAME}-${SF_VER}"
    UPSTREAM_FILE="${UPSTREAM}/${ROLE_NAME}-${SF_VER}"

    echo "${ROLE_NAME} local hash is ${ROLE_MD5}"

    # Make sure role tree is not mounted
    grep -q "${SF_VER}\/${ROLE_NAME}\/proc" /proc/mounts && {
        while true; do
            sudo umount ${INST}/${ROLE_NAME}/proc || break
        done
    }
    # Check if we can find roles built locally and that md5 is similar
    if [ -f "${ROLE_FILE}.md5" ] && [ "$(cat ${ROLE_FILE}.md5)" = "${ROLE_MD5}" ]; then
        echo "The locally built ${ROLE_NAME} md5 is similar to what we computed from your git branch state. Nothing to do"
        return
    fi
    # Check upstream role MD5 to know if upstream role can be re-used
    # Provide SKIP_UPSTREAM=1 to avoid checking the upstream pre-built role
    if [ -f "${UPSTREAM_FILE}.md5" ] && [ "$(cat ${UPSTREAM_FILE}.md5)" == "${ROLE_MD5}" ] && [ -z "$SKIP_UPSTREAM" ]; then
        echo "Upstream ${ROLE_NAME} md5 is similar to what we computed from your git branch state, I will use the upstream role."
        sudo rm -Rf ${INST}/${ROLE_NAME}
        sudo mkdir ${INST}/${ROLE_NAME}
        echo "Unarchive ..."
        sudo tar -xzf ${UPSTREAM_FILE}.edeploy -C "${INST}/${ROLE_NAME}"
        sudo touch ${INST}/${ROLE_NAME}.done
        echo ${ROLE_MD5} | sudo tee ${ROLE_FILE}.md5
        if [ -n "$VIRT" ]; then
            echo "Copy prebuilt qcow2 image ..."
            if [ -f ${UPSTREAM_FILE}.img.qcow2 ]; then
                sudo cp ${UPSTREAM_FILE}.img.qcow2 ${INST}/
            else
                # Should not be the case !
                echo "Prebuilt qcow2 image ${UPSTREAM_FILE}.img.qcow2 is not available upstream ! so build it."
                build_img ${ROLE_FILE} ${INST}/${ROLE_NAME} $IMG_CFG
            fi
        fi
    else
        if [ ! -f "${ROLE_FILE}.md5" ] || [ "$(cat ${ROLE_FILE}.md5)" != "${ROLE_MD5}" ]; then
            echo "The locally built ${ROLE_NAME} md5 is different to what we computed from your git branch state. I need to rebuild the role."
            sudo rm -f ${INST}/${ROLE_NAME}.done
            sudo ${MAKE} EDEPLOY_ROLES_PATH=${EDEPLOY_ROLES} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} ${ROLE_NAME}
            echo ${ROLE_MD5} | sudo tee ${ROLE_FILE}.md5
            if [ -n "$VIRT" ]; then
                echo "Upstream ${ROLE_NAME} is NOT similar ! I rebuild the qcow2 image."
                build_img ${ROLE_FILE} ${INST}/${ROLE_NAME} $IMG_CFG
            fi
        fi
    fi
}

function build_roles {
    [ ! -d "$BUILD_DIR/install/${DVER}-${SF_REL}" ] && sudo mkdir -p $BUILD_DIR/install/${DVER}-${SF_REL}

    # Clean the local copy before the md5 computations
    if [ -z "$(git ls-files -o -m --exclude-standard)" ]; then
        git clean -ffdx
    else
        echo "You have unstaged file in your local copy. Please stage them !"
        exit
    fi

    cd $SF_ROLES
    build_role "softwarefactory"   $(cd ..; find ${SF_DEPS} -type f | sort | xargs cat | md5sum | awk '{ print $1}')
    SFE=$?
    build_role "install-server-vm" $(cd ..; find ${IS_DEPS} -type f | sort | xargs cat | md5sum | awk '{ print $1}')
    IE=$?
}

prepare_buildenv
[ -z "$SKIP_UPSTREAM" ] && {
    [ -z "$SF_SKIP_FETCHBASES" ] && {
        ./fetch_roles.sh bases
        echo
    }
    ./fetch_roles.sh trees
    echo
    [ -n "$VIRT" ] && {
        ./fetch_roles.sh imgs
        echo
    }
}
fetch_edeploy
echo
build_roles

exit $[ $SFE + $IE ];
