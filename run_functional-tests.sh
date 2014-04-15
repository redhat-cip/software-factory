#!/bin/bash

set -x

function stop {
    if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
        cd lxc
        ./bootstrap-lxc.sh clean
        cd ..
    fi
}

echo -n > /tmp/debug
export SF_ROOT=$(pwd)
export SF_PREFIX=${SF_PREFIX:-tests}
export SKIP_CLEAN_ROLES="y"
export EDEPLOY_ROLES=/var/lib/sf/roles/

(cd lxc; ./bootstrap-lxc.sh clean)
sudo ./build_roles.sh

if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
    cd lxc
    ./bootstrap-lxc.sh
    cd ..
fi

# Start serverspec test to detect failure early
cp build/serverspec/hosts.yaml serverspec/
cd serverspec/
rake spec
RET=$?
[ "$RET" != "0" ] && {
    cd ..
    stop
    exit $RET
}
cd ..

nosetests -v ./tests
RET=$?
# This delay is used to wait a bit before fetching log file from hosts
# in order to not avoid so important logs that can appears some seconds
# after a failure.
sleep 30


echo "=================================================================================="
echo "===================================== DEBUG LOGS ================================="
echo "=================================================================================="
echo
echo "Gerrit logs content: --["
ssh root@${SF_PREFIX}-gerrit cat /home/gerrit/site_path/logs/*
echo "]--"
echo "Gerrit node /var/log/syslog content: --["
ssh root@${SF_PREFIX}-gerrit cat /var/log/syslog
echo "]--"
# The init option of gerrit.war will rewrite the gerrit config files
# if the provided files does not follow exactly the expected format by gerrit.
# If there is a rewrite puppet will detect the change in the *.config files
# and then trigger a restart. We want to avoid that because the gerrit restart
# can occured during functional tests. So here we display the changes that can
# appears in the config files (to help debugging).
# We have copied *.config files in /tmp just before the gerrit.war init (see the
# manifest) and create a diff after. Here we just display it to help debug.
echo "Gerrit configuration change: --["
ssh root@${SF_PREFIX}-gerrit cat /tmp/config.diff
echo "]--"
echo "MySQL node /var/log/syslog content: --["
ssh root@${SF_PREFIX}-mysql cat /var/log/syslog
echo "]--"
echo "Managesf node /var/log/syslog content: --["
ssh root@${SF_PREFIX}-managesf cat /var/log/syslog
echo "]--"
echo "Managesf node /var/log/apache2/error.log content: --["
ssh root@${SF_PREFIX}-managesf cat /var/log/apache2/error.log
echo "]--"
echo "Managesf node /tmp/debug logs content: --["
ssh root@${SF_PREFIX}-managesf cat /tmp/debug
echo "]--"
echo "Local /tmp/debug content: --["
cat /tmp/debug
echo "]--"
echo "local dmesg content: --["
sudo tail -n 50 /var/log/dmesg
echo "]--"

stop

exit $RET
