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

REFARCH="${1:-1node-allinone}"
TEST_TYPE="${2:-functional}"

###############
# Preparation #
###############
echo "Running functional-tests with this HEAD"
display_head
prepare_artifacts
checkpoint "Running tests on $(hostname)"
lxc_stop
[ -z "${SKIP_BUILD}" ] && {
    build_image
    prepare_functional_tests_venv
} || {
    dir=${INST}/softwarefactory
    sudo rsync -a --delete puppet/manifests/ ${dir}/etc/puppet/environments/sf/manifests/
    sudo rsync -a --delete puppet/modules/ ${dir}/etc/puppet/environments/sf/modules/
    sudo rsync -a --delete puppet/hiera/ ${dir}/etc/puppet/hiera/sf/
    sudo rsync -a --delete bootstraps/ ${dir}/root/bootstraps/
}

case "${TEST_TYPE}" in
    "functional")
        lxc_start
        run_bootstraps
        run_tests
        ;;
    "backup")
        lxc_start
        run_bootstraps
        run_backup_tests
        ;;
    "upgrade")
        echo "[+] Upgrade tests from 1.0.4 to 2.0.0 are not supported..."
        exit 1
        ;;
    "*")
        echo "[+] Unknown test type ${TEST_TYPE}"
        exit 1
        ;;
esac

DISABLE_SETX=1
checkpoint "end_tests"
# If run locally (outside of zuul) fetch logs/artifacts. If run
# through Zuul then a publisher will be used
[ -z "$SWIFT_artifacts_URL" ] && get_logs
[ -z "${DEBUG}" ] && lxc_stop
echo "$0: SUCCESS"
exit 0;
