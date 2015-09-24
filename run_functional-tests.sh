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
. role_configrc

echo "Running functional-tests with this HEAD"
display_head

# This prevent the bootstrap LXC script to set up IP MASQUERADE
# during the functional tests
export IN_FUNC_TESTS=1

function lxc_stop {
    (cd bootstraps/lxc; ./start.sh stop)
}

function build {
    clear_mountpoint
    # Retry to build role if it fails before exiting
    ./build_roles.sh ${ARTIFACTS_DIR} || ./build_roles.sh ${ARTIFACTS_DIR} || pre_fail "Roles building FAILED"
}

function lxc_start {
    clear_mountpoint
    (cd bootstraps/lxc; ./start.sh init) || pre_fail "LXC start FAILED"
}

set -x
prepare_artifacts
checkpoint "Running tests on $(hostname)"
lxc_stop
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
    echo "[+] Upgrade tests from 1.0.4 to 2.0.0 are not supported..."
    exit 1
fi

DISABLE_SETX=1
checkpoint "end_tests"
# If run locally (outside of zuul) fetch logs/artifacts. If run
# through Zuul then a publisher will be used
[ -z "$SWIFT_artifacts_URL" ] && {
    get_logs
    checkpoint "get-logs"
}
[ -z "${DEBUG}" ] && lxc_stop
checkpoint "lxc-stop"
clean_old_cache
echo "$0: SUCCESS"
exit 0;
