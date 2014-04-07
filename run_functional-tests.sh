#!/bin/bash

echo -n > /tmp/debug
export SF_ROOT=$(pwd)
export SF_PREFIX=tests
(cd lxc; ./bootstrap-lxc.sh clean)
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
