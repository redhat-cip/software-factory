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

set -e
[ -n "$DEBUG" ] && set -x
[ -n "$PB" ] && PB="--progress-bar" || PB="-s"

. ./role_configrc

[ -z "$1" ] || SF_VER=$1

function die {
    echo "[ERROR]: $1"
    exit -1
}

function fetch_sf_roles_prebuilt {
    echo "Fetch prebuilt SF roles ..."
    # Fetch last available SF roles
    local temp=$(mktemp -d /tmp/edeploy-check-XXXXX)
    for role in softwarefactory; do
        role=${role}-${SF_VER}
        if [ -f ${UPSTREAM}/${role}.edeploy ]; then
            echo "${UPSTREAM}/${role}.edeploy already exists..."
            continue
        fi
        curl -s -o ${temp}/${role}.md5 ${SWIFT_SF_URL}/${role}.md5 &> /dev/null || die "Could not fetch ${SWIFT_SF_URL}/${role}.md5"
        # Swift does not return 404 but 'Not Found'
        grep -q 'Not Found' ${temp}/${role}.md5 && die "${role} does not exist upstream"
        diff ${temp}/${role}.md5 ${UPSTREAM}/${role}.md5 &> /dev/null || {
            echo "Fetching ${role} ..."
            sudo curl $PB -o ${UPSTREAM}/${role}.edeploy ${SWIFT_SF_URL}/${role}.edeploy
            sudo curl -s -o ${UPSTREAM}/${role}.edeploy.md5 ${SWIFT_SF_URL}/${role}.edeploy.md5
            sudo mv -f ${temp}/${role}.md5 ${UPSTREAM}/${role}.md5
            role_md5=$(cat ${UPSTREAM}/${role}.edeploy | md5sum - | cut -d ' ' -f1)
            [ "${role_md5}" != "$(cat ${UPSTREAM}/${role}.edeploy.md5 | cut -d ' ' -f1)" ] && {
                echo "${role} archive md5 mismatch ! exit."
                rm -Rf ${temp}
                exit 1
            }
        } && echo "${role} is already synced"
    done
    rm -Rf ${temp}
}

function deflate_sf_roles_prebuilt {
    echo "Extract roles to ${INST}"
    for role in softwarefactory; do
        EXTRACT_DIR="${INST}/${role}"
        UPSTREAM_FILE="${UPSTREAM}/${role}-${SF_VER}.edeploy"
        if [ -d ${EXTRACT_DIR} ]; then
            echo "${EXTRACT_DIR} already exist..."
            continue
        fi
        sudo mkdir -p ${EXTRACT_DIR}
        echo "-> ${EXTRACT_DIR} (${UPSTREAM_FILE})"
        sudo tar -xzf ${UPSTREAM_FILE} -C "${EXTRACT_DIR}"
    done

}

prepare_buildenv
fetch_sf_roles_prebuilt
deflate_sf_roles_prebuilt
