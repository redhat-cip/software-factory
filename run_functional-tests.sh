#!/bin/bash

# This script will build the roles for SoftwareFactory
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

function get_ip {
    grep -B 1 "name:[ \t]*$1" /tmp/lxc-conf/sf-lxc.yaml | head -1 | awk '{ print $2 }'
}

source functestslib.sh

set -x

function stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        if [ ! ${DEBUG} ]; then
            cd bootstraps/lxc
            ./start.sh clean
            cd -
        fi
    fi
}

prepare_artifacts
clear_mountpoint

if [ ! ${SF_SKIP_BUILDROLES} ]; then
    ./build_roles.sh &> ${ARTIFACTS_DIR}/build_roles.sh.output || pre_fail "Roles building FAILED!"
fi

clear_mountpoint
if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
    cd bootstraps/lxc
    ./start.sh stop &> ${ARTIFACTS_DIR}/lxc-stop.output
    ./start.sh &> ${ARTIFACTS_DIR}/lxc-start.output || pre_fail "LXC bootstrap FAILED!"
    cd -
fi

run_tests 25
get_logs

set +x
stop

publish_artifacts

set -x
exit $[ ${ERROR_FATAL} + ${ERROR_RSPEC} + ${ERROR_TESTS} ]
