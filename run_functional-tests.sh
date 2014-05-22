#!/bin/bash

# This script will build the roles for SoftwareFactory
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

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

function get_ip {
    grep -B 1 "name:[ \t]*$1" /tmp/lxc-conf/sf-lxc.yaml | head -1 | awk '{ print $2 }'
}

function scan_and_configure_knownhosts {
    local ip=$1
    local port=$2
    ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$ip" > /dev/null 2>&1 || echo
    RETRIES=0
    echo " [+] Starting ssh-keyscan on $ip:$port"
    while true; do
        KEY=`ssh-keyscan -p $port $ip 2> /dev/null`
        if [ "$KEY" != ""  ]; then
            ssh-keyscan $ip 2> /dev/null >> "$HOME/.ssh/known_hosts"
            echo "  -> $role:$port is up!"
            break
        fi
        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && break
        echo "  [E] ssh-keyscan on $ip:$port failed, will retry in 5 seconds (attempt $RETRIES/40)"
        sleep 10
    done
}

function get_logs {
    #This delay is used to wait a bit before fetching log file from hosts
    #in order to not avoid so important logs that can appears some seconds
    #after a failure.
    sleep 30

    echo "=================================================================================="
    echo "===================================== DEBUG LOGS ================================="
    echo "=================================================================================="
    echo
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` cat /var/log/sf-bootstrap.log
    echo "Gerrit logs content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@gerrit.${SF_SUFFIX} cat /home/gerrit/site_path/logs/*"
    echo "]--"
    echo "Gerrit node /var/log/syslog content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@gerrit.${SF_SUFFIX} cat /var/log/syslog"
    echo "]--"
    # The init option of gerrit.war will rewrite the gerrit config files
    # if the provided files does not follow exactly the expected format by gerrit.
    # If there is a rewrite puppet will detect the change in the *.config files
    # and then trigger a restart. We want to avoid that because the gerrit restart
    # can occured during functional tests. So here we display the changes that can
    # appears in the config files (to help debugging).
    # We have copied *.config files in /tmp just before the gerrit.war init (see the
    # manifest) and create a diff after. Here we just display it to help debug.
    echo "Redmine node /var/log/redmine/default/production.log content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@redmine.${SF_SUFFIX} cat /var/log/redmine/default/production.log"
    echo "]--"
    echo "Gerrit configuration change: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@gerrit.${SF_SUFFIX} cat /tmp/config.diff"
    echo "]--"
    echo "MySQL node /var/log/syslog content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@mysql.${SF_SUFFIX} cat /var/log/syslog"
    echo "]--"
    echo "Managesf node /var/log/syslog content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@managesf.${SF_SUFFIX} cat /var/log/syslog"
    echo "]--"
    echo "Managesf node /var/log/apache2/error.log content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@managesf.${SF_SUFFIX} cat /var/log/apache2/error.log"
    echo "]--"
    echo "Managesf node /tmp/debug logs content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "ssh root@managesf.${SF_SUFFIX} cat /tmp/debug"
    echo "]--"
    echo "Local /tmp/debug content: --["
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` cat /tmp/debug
    echo "]--"
}

export SF_SUFFIX=${SF_SUFFIX:-tests.dom}
export SKIP_CLEAN_ROLES="y"
export EDEPLOY_ROLES=/var/lib/sf/roles/

if [ ! ${SF_SKIP_BUILDROLES} ]; then
    ./build_roles.sh
fi

if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
    cd bootstraps/lxc
    ./start.sh stop
    ./start.sh
    cd -
fi

scan_and_configure_knownhosts `get_ip puppetmaster` 22

retries=0
while true; do
    # We wait for the bootstrap script that run on puppetmaster node finish its work
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` test -f puppet-bootstrapper/build/bootstrap.done 
    [ "$?" -eq "0" ] && break
    let retries=retries+1
    if [ "$retries" == "30" ]; then
        get_logs
        stop
        exit 1
    fi
    sleep 30
done

retries=0
while true; do
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper/serverspec/; rake spec"
    RET=$?
    [ "$RET" == "0" ] && break
        let retries=retries+1
        if [ "$retries" == "5" ]; then
            get_logs
            stop
            exit $RET
        fi
    sleep 10
done

ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper; SF_SUFFIX=${SF_SUFFIX} SF_ROOT=\$(pwd) nosetests -v"
RET=$?

get_logs
stop
exit $RET
