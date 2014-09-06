#!/bin/bash
# This script will build the roles for SoftwareFactory
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

source functestslib.sh

echo "Running functional-tests with this HEAD"
display_head

function lxc_stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        if [ ! ${DEBUG} ]; then
            (cd bootstraps/lxc; ./start.sh clean &> ${ARTIFACTS_DIR}/lxc-clean.output)
        fi
    fi
}

function build {
    if [ ! ${SF_SKIP_BUILDROLES} ]; then
        clear_mountpoint
        ./build_roles.sh &> ${ARTIFACTS_DIR}/build_roles.sh.output || pre_fail "Roles building FAILED"
    fi
}

function lxc_start {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        clear_mountpoint
        cd bootstraps/lxc
        ./start.sh stop &> ${ARTIFACTS_DIR}/lxc-stop.output
        ./start.sh &> ${ARTIFACTS_DIR}/lxc-start.output || pre_fail "LXC bootstrap FAILED"
        cd -
    fi
}

set -x
prepare_artifacts
checkpoint "$(date) - $(hostname)"
(cd bootstraps/lxc; ./start.sh clean &> ${ARTIFACTS_DIR}/lxc-first-clean.output)
checkpoint "lxc-first-clean"
build
checkpoint "build_roles"
lxc_start
checkpoint "lxc-start"
if [ -z "$1" ]; then
    # This test is run by default when no argument provided
    run_tests 45
    checkpoint "run_tests"
fi
if [ "$1" == "backup_restore_tests" ]; then
    run_backup_restore_tests 45 "provision" || pre_fail "Backup test: provision"
    lxc_stop
    if [ "$ERROR_PC" == "0" ] && [ "$ERROR_FATAL" == "0" ] && [ "$ERROR_RSPEC" == "0" ]; then
        # No error occured at provision so continue
        lxc_start
        run_backup_restore_tests 45 "check" || pre_fail "Backup test: check"
    fi
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
