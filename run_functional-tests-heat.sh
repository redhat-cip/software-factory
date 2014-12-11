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

source /etc/sf-dom-enocloud.openrc

[ -z "$HEAT_TENANT" ] && {
    echo "HEAT_TENANT is empty ... have you sourced an openrc ?"
    exit 1
}
echo "Use $HEAT_TENANT on $OS_AUTH_URL"
export OS_TENANT_NAME=${HEAT_TENANT}
unset OS_TENANT_ID
source functestslib.sh

echo "Running functional-tests with this HEAD"
display_head

set -x

export STACKNAME=SoftwareFactory

function get_ip {
    while true; do
        p=`nova list | grep ${STACKNAME}-puppetmaster | cut -d'|' -f7  | awk '{print $NF}' | sed "s/ //g"`
        [ -n "$p" ] && break
        sleep 10
    done
    echo $p
}

function waiting_stack_deleted {
    while true; do
        heat stack-list | grep -i $STACKNAME | grep -i failed
        [ "$?" -eq "0" ] && {
            echo "Stack deletion has failed ..."
            return 255
        }
        heat stack-list | grep -i $STACKNAME
        [ "$?" != "0" ] && break
        sleep 60
    done
}

function heat_stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        if [ ! ${DEBUG} ]; then
            cd bootstraps/heat
            ./start.sh delete_stack
            waiting_stack_deleted
            if [ "$?" = "255" ]; then
                # Retry a deletion call
                ./start.sh delete_stack
                waiting_stack_deleted
            fi
            cd -
        fi
    fi
}

function build_imgs {
    if [ ! ${SF_SKIP_BUILDROLES} ]; then
        VIRT=1 ./build_roles.sh &> ${ARTIFACTS_DIR}/build_roles.sh.output || pre_fail "Roles building FAILED"
    fi
}

function heat_start {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        cd bootstraps/heat
        ./start.sh full_restart_stack
        cd -
    fi
}

function glance_delete_images {
    cd bootstraps/heat
    ./start.sh delete_images
    cd -
}

set -x
prepare_artifacts
checkpoint "$(date) - $(hostname)"
build_imgs
checkpoint "build_roles"
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
exit 0;
