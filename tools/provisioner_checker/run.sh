#!/bin/bash

# An environment is needed to run the checker or provision python
# tool. This script is made for that : ./run.sh checker or ./run.sh provisioner

set -x

cur=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
. ${cur}/../../functestslib.sh

SF_ROOT=${SF_ROOT:-"/root/puppet-bootstrapper"}
SF_SUFFIX=${SF_SUFFIX:-"tests.dom"}

function run {
    local cmd=$1
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@192.168.134.54` "cd puppet-bootstrapper/tools/provisioner_checker; SF_SUFFIX=${SF_SUFFIX} SF_ROOT=${SF_ROOT} python $cmd.py"
    ERROR=$?
}

run $1
exit $[ ${ERROR} ]
