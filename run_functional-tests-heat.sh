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

# This script will build if needed the roles for software-factory
# Then will start the SF using the HEAT deployment way
# Then will run the serverspecs and functional tests




###########  WARNING ########################################
# To run that test on your HEAT account please create a file
# called sf-dom-enocloud.openrc with that content:
#
# export OS_AUTH_URL=auth_url_to_replace
# export OS_TENANT_NAME="tenant_name_to_replace"
# export OS_PASSWORD="your_password_to_replace"
# export OS_USERNAME="username-to_replace"
# export HEAT_TENANT=${OS_TENANT_NAME}
# export NOVA_KEYNAME=name_of_the_keypair_to_use
#############################################################

source /etc/sf-dom-enocloud.openrc

[ -z "$HEAT_TENANT" ] && {
    echo "HEAT_TENANT is empty ... have you sourced an openrc ?"
    exit 1
}
echo "Use $HEAT_TENANT on $OS_AUTH_URL"
export OS_TENANT_NAME=${HEAT_TENANT}
unset OS_TENANT_ID
export NOVA_KEYNAME=${NOVA_KEYNAME-$HEAT_TENANT}
export FORMAT=raw
source functestslib.sh

echo "Running functional-tests with this HEAD"
display_head

set -x

export STACKNAME=SoftwareFactory

function check_keypair {
    LOCAL_FINGERPRINT=$(ssh-keygen -l -f ~/.ssh/id_rsa | awk '{ print $2 }')
    NOVA_KEYPAIR=$(nova keypair-list | grep ${NOVA_KEYNAME} | awk '{ print $4 }')

    if [ -z "${NOVA_KEYPAIR}" ]; then
        echo "Creating a new keypair for ${HEAT_TENANT}"
        nova keypair-add --pub-key ~/.ssh/id_rsa.pub ${NOVA_KEYNAME}
    elif [ "${NOVA_KEYPAIR}" != "${LOCAL_FINGERPRINT}" ]; then
        echo "Replacing old keypair for ${HEAT_TENANT}"
        nova keypair-delete ${NOVA_KEYNAME}
        nova keypair-add --pub-key ~/.ssh/id_rsa.pub ${NOVA_KEYNAME}
    fi
}

function get_ip {
    wait_for_statement "nova list | grep ${STACKNAME}-puppetmaster | cut -d'|' -f7  | awk '{print $NF}' | sed 's/ //g' | grep [0-9]"
    nova list | grep ${STACKNAME}-puppetmaster | cut -d'|' -f7  | awk '{print $NF}' | sed "s/ //g"
}

function waiting_stack_deleted {
    wait_for_statement "heat stack-show ${STACKNAME} &> /dev/null" 1
}

function heat_stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        if [ ! ${DEBUG} ]; then
            heat stack-delete ${STACKNAME}
            waiting_stack_deleted || {
                # Sometime delete failed and needs to be retriggered...
                heat stack-delete ${STACKNAME}
                waiting_stack_deleted
            }
        fi
    fi
}

function build_imgs {
    if [ ! ${SF_SKIP_BUILDROLES} ]; then
        VIRT=1 ./build_roles.sh ${ARTIFACTS_DIR} || pre_fail "Roles building FAILED"
    fi
}

function heat_start {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        (cd bootstraps/heat; ./start.sh full_restart_stack)
    fi
}

function glance_delete_images {
    if [ ! ${DEBUG} ]; then
        (cd bootstraps/heat; ./start.sh delete_images)
    fi
}

function check_clean_environment {
    heat stack-show ${STACKNAME} &> /dev/null && {
        heat_stop
    }
}

set -x
prepare_artifacts
checkpoint "Running heat tests on $(hostname)"
build_imgs
checkpoint "build_roles"
check_keypair
check_clean_environment
heat_start
checkpoint "heat_start"
waiting_stack_created $STACKNAME
checkpoint "wait_heat_stack"
run_tests 15
checkpoint "run_tests"
DISABLE_SETX=1
checkpoint "end_tests"
get_logs
checkpoint "get-logs"
heat_stop
checkpoint "heat_stop"
glance_delete_images
checkpoint "glance_delete_images"
publish_artifacts
checkpoint "publish-artifacts"
clean_old_cache
exit 0;
