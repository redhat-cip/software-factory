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

. ./role_configrc

function fetch_base_roles_prebuilt {
    # Fetch edeploy and edeploy-roles (to fetch master EDEPLOY_ROLES_REL)
    echo "Fetch edeploy and edeploy-roles project from github ..."
    fetch_edeploy
    echo "Fetch prebuilt bases edeploy roles (cloud and install-server) ..."
    # Prepare prebuild roles
    local temp=$(mktemp -d /tmp/edeploy-check-XXXXX)
    PREBUILD_TARGET=$WORKSPACE/roles/install/$EDEPLOY_ROLES_REL
    [ ! -d $PREBUILD_TARGET ] && {
        sudo mkdir -p $PREBUILD_TARGET
        sudo chown ${USER}:root $PREBUILD_TARGET
    }
    cloud_img="cloud-$EDEPLOY_ROLES_REL.edeploy"
    install_server_img="install-server-$EDEPLOY_ROLES_REL.edeploy"

    # Check if edeploy roles are up-to-date
    [ ! -f $PREBUILD_TARGET/$install_server_img.md5 ] && sudo touch $PREBUILD_TARGET/$install_server_img.md5
    [ ! -f $PREBUILD_TARGET/$cloud_img.md5 ] && sudo touch $PREBUILD_TARGET/$cloud_img.md5
    curl -s -o ${temp}/$install_server_img.md5 ${BASE_URL}/$install_server_img.md5
    curl -s -o ${temp}/$cloud_img.md5 ${BASE_URL}/$cloud_img.md5
    diff $PREBUILD_TARGET/$install_server_img.md5 ${temp}/$install_server_img.md5 || {
        echo "Fetching $install_server_img ..."
        curl --progress-bar -o ${temp}/$install_server_img ${BASE_URL}/$install_server_img
        sudo mv -f ${temp}/$install_server_img* $PREBUILD_TARGET
        # Remove the previously unziped archive
        [ -d $PREBUILD_TARGET/install-server ] && sudo rm -Rf $PREBUILD_TARGET/install-server
    } && echo "$install_server_img is already synced"
    diff $PREBUILD_TARGET/$cloud_img.md5 ${temp}/$cloud_img.md5 || {
        echo "Fetching $cloud_img ..."
        curl --progress-bar -o ${temp}/$cloud_img ${BASE_URL}/$cloud_img
        sudo mv -f ${temp}/$cloud_img* $PREBUILD_TARGET
        # Remove the previously unziped archive
        [ -d $PREBUILD_TARGET/cloud ] && sudo rm -Rf $PREBUILD_TARGET/cloud
    } && echo "$cloud_img is already synced"
    # Uncompress prebuild images if needed
    cd $PREBUILD_TARGET
    [ ! -d cloud ] && {
        echo "Unarchive the cloud base role ..."
        sudo mkdir cloud
        sudo tar -xzf $cloud_img -C cloud
        sudo touch cloud.done
    }
    [ ! -d install-server ] && {
        echo "Unarchive the install-server base role ..."
        sudo mkdir install-server
        sudo tar -xzf $install_server_img -C install-server
        sudo touch install-server.done
    }
    cd - > /dev/null
    rm -Rf ${temp}
}

function fetch_sf_roles_prebuilt {
    echo "Fetch prebuilt SF roles ..."
    # Fetch last available SF roles
    local temp=$(mktemp -d /tmp/edeploy-check-XXXXX)
    for role in mysql slave install-server-vm softwarefactory; do
        role=${role}-${SF_VER}
        curl -s -o ${temp}/${role}.md5 ${BASE_URL}/${role}.md5 &> /dev/null || continue
        # Swift does not return 404 but 'Not Found'
        grep -q 'Not Found' ${temp}/${role}.md5 && { echo "${role} does not exist upstream"; continue; }
        diff ${temp}/${role}.md5 ${UPSTREAM}/${role}.md5 &> /dev/null || {
            echo "Fetching ${role} ..."
            sudo curl --progress-bar -o ${UPSTREAM}/${role}.edeploy ${BASE_URL}/${role}.edeploy
            sudo curl -s -o ${UPSTREAM}/${role}.edeploy.md5 ${BASE_URL}/${role}.edeploy.md5
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

function fetch_sf_qcow2_roles_prebuilt {
    echo "Fetch prebuilt SF roles images (qcow2) ..."
    # Fetch last available SF roles
    local temp=$(mktemp -d /tmp/edeploy-check-XXXXX)
    for role in mysql slave install-server-vm softwarefactory; do
        role=${role}-${SF_VER}.qcow2
        curl -s -o ${temp}/${role}.md5 ${BASE_URL}/${role}.md5 || continue
        # Swift does not return 404 but 'Not Found'
        grep -q 'Not Found' ${temp}/${role}.md5 && { echo "${role} does not exist upstream"; continue; }
        diff ${temp}/${role}.md5 ${UPSTREAM}/${role}.md5 &> /dev/null || {
            echo "Fetching ${role} image ..."
            sudo curl --progress-bar -o ${UPSTREAM}/${role} ${BASE_URL}/${role}
            sudo curl -s -o ${UPSTREAM}/${role}.md5 ${BASE_URL}/${role}.md5
            sudo mv -f ${temp}/${role}.md5 ${UPSTREAM}/${role}.md5
            qcow2_md5=$(cat ${UPSTREAM}/${role} | md5sum - | cut -d ' ' -f1)
            [ "${qcow2_md5}" != "$(cat ${UPSTREAM}/${role}.md5 | cut -d ' ' -f1)" ] && {
                echo "${role} image md5 mismatch ! exit."
                rm -Rf ${temp}
                exit 1
            }
        } && echo "${role} image is already synced"
    done
    rm -Rf ${temp}
}

prepare_buildenv
[ "$1" == "bases" ] && fetch_base_roles_prebuilt || true
[ "$1" == "trees" ] && fetch_sf_roles_prebuilt || true
[ "$1" == "imgs" ] && fetch_sf_qcow2_roles_prebuilt || true
