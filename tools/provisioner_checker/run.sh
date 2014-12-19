#!/bin/bash

# An environment is needed to run the checker or provision python
# tool. This script is made for that : ./run.sh checker or ./run.sh provisioner

set -x

SF_ROOT=${SF_ROOT:-"/root/puppet-bootstrapper"}
SF_SUFFIX=${SF_SUFFIX:-"tests.dom"}
CONFDIR=/var/lib/lxc-conf

function get_ip {
    grep -B 1 "name:[ \t]*$1" ${CONFDIR}/sf-lxc.yaml | head -1 | awk '{ print $2 }'
}

function run {
    local cmd=$1
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@`get_ip puppetmaster` "cd puppet-bootstrapper/tools/provisioner_checker; SF_SUFFIX=${SF_SUFFIX} SF_ROOT=${SF_ROOT} python $cmd.py"
    ERROR=$?
}

run $1
exit $[ ${ERROR} ]
