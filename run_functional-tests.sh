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
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

source functestslib.sh

echo "Running functional-tests with this HEAD"
display_head

function lxc_stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        if [ ! ${DEBUG} ]; then
            (cd bootstraps/lxc; ./start.sh destroy &> ${ARTIFACTS_DIR}/lxc-clean.output)
        fi
    fi
}

function build {
    if [ ! ${SF_SKIP_BUILDROLES} ]; then
        clear_mountpoint
        ./build_roles.sh ${ARTIFACTS_DIR} || pre_fail "Roles building FAILED"
    fi
}

function lxc_start {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        clear_mountpoint
        cd bootstraps/lxc
        ./start.sh destroy &> ${ARTIFACTS_DIR}/lxc-stop.output
        ./start.sh init &> ${ARTIFACTS_DIR}/lxc-start.output || pre_fail "LXC bootstrap FAILED"
        cd -
    fi
}

set -x
prepare_artifacts
checkpoint "$(date) - $(hostname)"
(cd bootstraps/lxc; ./start.sh destroy &> ${ARTIFACTS_DIR}/lxc-first-clean.output)
checkpoint "lxc-first-clean"
build
checkpoint "build_roles"
if [ -z "$1" ]; then
    # This test is run by default when no argument provided
    lxc_start
    checkpoint "lxc-start"
    run_tests 15
    checkpoint "run_tests"
fi
if [ "$1" == "backup_restore_tests" ]; then
    lxc_start
    checkpoint "lxc-start"
    run_backup_restore_tests 45 "provision" || pre_fail "Backup test: provision"
    lxc_stop
    lxc_start
    run_backup_restore_tests 45 "check" || pre_fail "Backup test: check"
fi
if [ "$1" == "upgrade" ]; then
    # Try to load role_configrc here to SF_REL and SF_PREVIOUS_REL
    cloned=/tmp/software-factory # The place to clone the previous SF version to deploy
    (
        [ -d $cloned ] && rm -Rf $cloned
        git clone http://softwarefactory.enovance.com/r/software-factory $cloned
        cd $cloned
        # Be sure to checkout the right previous version
        git checkout 0.9.2
        # Fetch the pre-built images
        ./fetch_roles.sh trees
        # Trigger a build role in order to deflate roles in the right directory if not done yet
        SF_SKIP_FETCHBASES=1 ./build_roles.sh
        cd bootstraps/lxc
        # Deploy
        ./start.sh
        cd ../..
        source functestslib.sh
        wait_for_bootstrap_done
        # Run basic tests
        run_serverspec
    ) || pre_fail "Stable Bootstrap FAILED"
    # Run the provisioner to put some data on the deployed instance
    ./tools/provisioner_checker/run.sh provisioner
    # Put needed data to perform the upgrade on the deployed instance
    # In a real upgrade process this won't be done because next version
    # (The one we want to upgrade is already published)
    (
        cd tests/roles_provision/
        sudo ./prepare.sh
        export ANSIBLE_HOST_KEY_CHECKING=False
        ansible-playbook --private-key=${HOME}/.ssh/id_rsa -i inventory playbook.yaml
    ) || pre_fail "Ansible provision playbook FAILED"
    # Start the upgrade
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd /srv/software-factory/ && ./upgrade.sh 0.9.4 true" || pre_fail "Upgrade FAILED"
    # Run basic tests
    run_serverspec || pre_fail "Serverspec failed"
    # Run the checker to validate provisionned data has not been lost
    ./tools/provisioner_checker/run.sh checker || pre_fail "Provisionned data check failed"
fi

DISABLE_SETX=1
checkpoint "end_tests"
get_logs
checkpoint "get-logs"
lxc_stop
checkpoint "lxc-stop"
publish_artifacts
checkpoint "publish-artifacts"
exit 0;
