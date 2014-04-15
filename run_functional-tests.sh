#!/bin/bash

set -x

echo -n > /tmp/debug
export SF_ROOT=$(pwd)
export SF_PREFIX=tests
export SKIP_CLEAN_ROLES="y"
export EDEPLOY_ROLES=/var/lib/sf/roles/
(cd lxc; ./bootstrap-lxc.sh clean)
./build_roles.sh || exit -1
nosetests -v ./tests
RET=$?
echo "=================================================================================="
echo "===================================== DEBUG LOGS ================================="
echo "=================================================================================="
echo
echo "Gerrit logs content: --["
ssh root@${SF_PREFIX}-gerrit cat /home/gerrit/site_path/logs/*
echo "]--"
echo
echo "/tmp/debug content: --["
cat /tmp/debug
echo "]--"

(cd lxc; ./bootstrap-lxc.sh clean)
exit $RET
