#!/bin/bash

# This script will build the roles for SoftwareFactory
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

function get_ip {
    while true; do
        p=`nova list | grep puppetmaster | cut -d'|' -f7  | awk '{print $NF}' | sed "s/ //g"`
        [ -n "$p" ] && break
        sleep 10
    done
    echo $p
}

source functestslib.sh

set -x

function stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        if [ ! ${DEBUG} ]; then
            cd bootstraps/heat
            ./start.sh delete_stack
            cd -
        fi
    fi
}

prepare_artifacts

if [ ! ${SF_SKIP_BUILDROLES} ]; then
    VIRT=1 ./build_roles.sh &> ${ARTIFACTS_DIR}/build_roles.sh.output || pre_fail "Roles building FAILED!"
fi

if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
    cd bootstraps/heat
    ./start.sh full_restart_stack
    cd -
fi

waiting_stack_created
run_tests 60
get_logs

set +x
stop

publish_artifacts

set -x
exit $[ ${ERROR_FATAL} + ${ERROR_RSPEC} + ${ERROR_TESTS} ]
