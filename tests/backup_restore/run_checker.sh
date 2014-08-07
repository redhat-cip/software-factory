#!/bin/bash

# This script will run the checker tool

set -x

SF_ROOT=${SF_ROOT:-"/root/puppet-bootstrapper"}
SF_SUFFIX=${SF_SUFFIX:-"tests.com"}

function get_ip {
    grep -B 1 "name:[ \t]*$1" /tmp/lxc-conf/sf-lxc.yaml | head -1 | awk '{ print $2 }'
}

function run_checker {
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@`get_ip puppetmaster` "cd puppet-bootstrapper/tools/provisioner_checker; SF_SUFFIX=${SF_SUFFIX} SF_ROOT=${SF_ROOT} python checker.py"
    ERROR_CHECKER=$?
}

run_checker
exit $[ ${ERROR_CHECKER} ]
