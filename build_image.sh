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
function wait_for_lock {
    retry=0
    while [ $retry -lt 360 ]; do
        [ -f ${LOCK} ] || return
        echo "Lock file present: ${LOCK}"
        sleep 1;
        let retry=retry+1
    done
    exit -1
}

function put_lock {
    sudo touch ${LOCK}
    trap "sudo rm -f ${LOCK}" EXIT
}

wait_for_lock
put_lock

. ./role_configrc
[ -z "$DEBUG" ] || set -x

function description_diff {
    sudo curl -o ${IMAGE_PATH}.old_description ${SWIFT_SF_URL}/softwarefactory-${SF_VER}.description
    # Can't find current version description, tries previous_ver
    grep -q "Not Found" ${IMAGE_PATH}.old_description && sudo curl -o ${IMAGE_PATH}.old_description ${SWIFT_SF_URL}/softwarefactory-${SF_PREVIOUS_VER}.description
    grep -q "Not Found" ${IMAGE_PATH}.old_description && echo "(E) Couldn't find previous description"
    diff ${IMAGE_PATH}.old_description ${IMAGE_PATH}-${SF_VER}.description | sudo tee ${IMAGE_PATH}.description_diff
}

function build_qcow {
    IMAGE_FILE="${IMAGE_PATH}-${SF_VER}.img"
    [ -f "${IMAGE_FILE}" ] && sudo rm -Rf ${IMAGE_FILE}
    [ -f "${IMAGE_FILE}.qcow2" ] && sudo rm -Rf "${IMAGE_FILE}.qcow2"

    sudo ./image/create-image.sh ${IMAGE_PATH} ${IMAGE_FILE} ./image/params.virt || failure=1
    # Remove the raw image, only keep the qcow2 image
    sudo rm -f ${IMAGE_FILE} ${IMAGE_FILE}.md5
    if [ "$failure" == 1 ]; then
        echo "(STEP2) FAILED"
        exit 1
    fi
}

function build_image {
    if test -L ${IMAGE_PATH}/usr/bin/yum; then
        echo "(STEP1) Old image detected, removing it"
        sudo rm -Rf ${IMAGE_PATH}
    fi

    if [ ! -d ${IMAGE_PATH} ]; then
        echo "(STEP1) Image not found, rebuilding from scratch"
        # TODO: add function to fetch last build
        sudo mkdir -p ${IMAGE_PATH}
    fi

    (
        set -e
        cd image
        DOCDIR=$DOCDIR MANAGESF_CLONED_PATH=$MANAGESF_CLONED_PATH PYSFLIB_CLONED_PATH=$PYSFLIB_CLONED_PATH \
        CAUTH_CLONED_PATH=$CAUTH_CLONED_PATH SFMANAGER_CLONED_PATH=$SFMANAGER_CLONED_PATH \
        SF_REPO=${SF_REPO} sudo -E ./softwarefactory.install ${IMAGE_PATH} ${SF_VER}
        ./get_image_versions_information.sh ${IMAGE_PATH} | sudo tee ${IMAGE_PATH}-${SF_VER}.description > /dev/null
    )
    if [ "$?" != "0" ]; then
        echo "(STEP1) FAILED"
        exit 1
    fi
    echo "(STEP1) SUCCESS ${IMAGE_PATH}"
    description_diff
}

prepare_buildenv
# Make sure subproject are available
echo "(STEP0) Fetch subprojects..."
./image/fetch_subprojects.sh || exit 1
build_image
if [ -n "$BUILD_QCOW" ]; then
    echo "(STEP2) Building qcow, please wait..."
    build_qcow
fi
