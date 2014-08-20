#!/bin/bash

# This script will build the roles for SoftwareFactory
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

function get_ip {
    grep -B 1 "name:[ \t]*$1" /tmp/lxc-conf/sf-lxc.yaml | head -1 | awk '{ print $2 }'
}

source functestslib.sh


function stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        if [ ! ${DEBUG} ]; then
            cd bootstraps/lxc
            ./start.sh clean &> ${ARTIFACTS_DIR}/lxc-clean.output
            cd -
        fi
    fi
}

function build {
    if [ ! ${SF_SKIP_BUILDROLES} ]; then
        clear_mountpoint
        ./build_roles.sh &> ${ARTIFACTS_DIR}/build_roles.sh.output || pre_fail "Roles building FAILED!"
    fi
}

function start {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        clear_mountpoint
        cd bootstraps/lxc
        ./start.sh stop &> ${ARTIFACTS_DIR}/lxc-stop.output
        ./start.sh &> ${ARTIFACTS_DIR}/lxc-start.output || pre_fail "LXC bootstrap FAILED!"
        cd -
    fi
}

set -x
prepare_artifacts
checkpoint "$(date) - $(hostname)"
build
checkpoint "build_roles"
start
checkpoint "lxc-start"
if [ -z "$1" ]; then
    # This test is run by default when no argument provided
    run_tests 25
    checkpoint "run_tests"
fi
if [ "$1" == "backup_restore_tests" ]; then
    run_backup_restore_tests 25 "provision"
    stop
    if [ "$ERROR_PC" == "0" ] && [ "$ERROR_FATAL" == "0" ] && [ "$ERROR_RSPEC" == "0" ]; then
        # No error occured at provision so continue
        start
        run_backup_restore_tests 25 "check"
    fi
fi
checkpoint "test-done"
get_logs
checkpoint "get-logs"
set +x
host_debug
stop
checkpoint "lxc-stop"
publish_artifacts
checkpoint "publish-artifacts"
set -x
exit $[ ${ERROR_FATAL} + ${ERROR_RSPEC} + ${ERROR_TESTS} + ${ERROR_PC} ]
