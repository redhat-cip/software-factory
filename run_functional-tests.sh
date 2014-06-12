#!/bin/bash

# This script will build the roles for SoftwareFactory
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

set -x

JENKINS_URL=46.231.128.203
GERRIT_PROJECT=${GERRIT_PROJECT-sf}
CURRENT_BRANCH=`git branch | sed -n -e 's/^\* \(.*\)/\1/p'`
# If run outside Jenkins use the current branch name
GERRIT_CHANGE_NUMBER=${GERRIT_CHANGE_NUMBER-$CURRENT_BRANCH}
GERRIT_PATCHSET_NUMBER=${GERRIT_PATCHSET_NUMBER-0}
[ "$USER" = "jenkins" ] && GROUP="www-data" || GROUP="$USER"

ARTIFACTS_RELPATH=$(
    echo logs/$(date '+%Y-%m')/${GERRIT_PROJECT}/${GERRIT_CHANGE_NUMBER}/${GERRIT_PATCHSET_NUMBER} | \
        sed 's/[ \t\n\r\.]//g'
)
ARTIFACTS_ROOT="/var/lib/sf/artifacts"
ARTIFACTS_DIR="${ARTIFACTS_ROOT}/${ARTIFACTS_RELPATH}"

function prepare_artifacts {
    [ -d ${ARTIFACTS_DIR} ] && sudo rm -Rf ${ARTIFACTS_DIR}
    sudo mkdir -p ${ARTIFACTS_DIR}
    sudo chown -R $USER:$GROUP ${ARTIFACTS_ROOT}
    echo "Logs will be available here: http://${JENKINS_URL}:8081/${ARTIFACTS_RELPATH}"
}

function publish_artifacts {
    find ${ARTIFACTS_DIR} -type d -exec chmod 550 {} \;
    find ${ARTIFACTS_DIR} -type f -exec chmod 440 {} \;
    sudo chown -R $USER:$GROUP ${ARTIFACTS_DIR}
    echo "Logs are available here: http://${JENKINS_URL}:8081/${ARTIFACTS_RELPATH}"
}

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
        echo "  [E] ssh-keyscan on $ip:$port failed, will retry in 20 seconds (attempt $RETRIES/40)"
        sleep 20
    done
}

function get_logs {
    #This delay is used to wait a bit before fetching log file from hosts
    #in order to not avoid so important logs that can appears some seconds
    #after a failure.
    sleep 30
    O=${ARTIFACTS_DIR}

    echo "=================================================================================="
    echo "================================== FETCHING LOGS ================================="
    echo "=================================================================================="
    echo
    scp    -o StrictHostKeyChecking=no root@`get_ip puppetmaster`:/var/log/sf-bootstrap.log $O/ 2> /dev/null

    for role in gerrit redmine jenkins mysql managesf commonservices ldap; do
        mkdir $O/${role}
        scp -o StrictHostKeyChecking=no root@`get_ip ${role}`:/var/log/syslog $O/${role}  2> /dev/null
    done

    scp -r -o StrictHostKeyChecking=no root@`get_ip gerrit`:/home/gerrit/site_path/logs/ $O/gerrit/ 2> /dev/null
    scp    -o StrictHostKeyChecking=no root@`get_ip gerrit`:/tmp/config.diff $O/gerrit/ 2> /dev/null
    # The init option of gerrit.war will rewrite the gerrit config files
    # if the provided files does not follow exactly the expected format by gerrit.
    # If there is a rewrite puppet will detect the change in the *.config files
    # and then trigger a restart. We want to avoid that because the gerrit restart
    # can occured during functional tests. So here we display the changes that can
    # appears in the config files (to help debugging).
    # We have copied *.config files in /tmp just before the gerrit.war init (see the
    # manifest) and create a diff after. Here we just display it to help debug.

    scp    -o StrictHostKeyChecking=no root@`get_ip redmine`:/var/log/redmine/default/production.log $O/redmine/ 2> /dev/null

    scp    -o StrictHostKeyChecking=no root@`get_ip managesf`:/var/log/managesf/managesf.log $O/managesf/ 2> /dev/null
    scp -r -o StrictHostKeyChecking=no root@`get_ip managesf`:/var/log/apache2/ $O/managesf/ 2> /dev/null

    scp    -o StrictHostKeyChecking=no root@`get_ip puppetmaster`:/tmp/debug $O/puppetmaster/ 2> /dev/null
}

export SF_SUFFIX=${SF_SUFFIX:-tests.dom}
export SKIP_CLEAN_ROLES="y"
export EDEPLOY_ROLES=/var/lib/sf/roles/

prepare_artifacts

function pre_fail {
    set +x
    echo $1
    stop &> /dev/null
    publish_artifacts
    exit 1
}

if [ ! ${SF_SKIP_BUILDROLES} ]; then
    ./build_roles.sh &> ${ARTIFACTS_DIR}/build_roles.sh.output || pre_fail "Roles building FAILED!"
fi

if [ ! ${SF_SKIP_BOOTSTRAP} ]; then
    cd bootstraps/lxc
    ./start.sh stop &> ${ARTIFACTS_DIR}/lxc-stop.output
    ./start.sh &> ${ARTIFACTS_DIR}/lxc-start.output || pre_fail "LXC bootstrap FAILED!"
    cd -
fi

scan_and_configure_knownhosts `get_ip puppetmaster` 22

ERROR_FATAL=0
ERROR_RSPEC=0
ERROR_TESTS=0

retries=0
while true; do
    # We wait for the bootstrap script that run on puppetmaster node finish its work
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` test -f puppet-bootstrapper/build/bootstrap.done
    [ "$?" -eq "0" ] && break
    let retries=retries+1
    if [ "$retries" == "15" ]; then
        ERROR_FATAL=1
        break
    fi
    sleep 60
done

retries=0
while true; do
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper/serverspec/; rake spec"
    RET=$?
    [ "$RET" == "0" ] && break
        let retries=retries+1
        if [ "$retries" == "5" ]; then
            ERROR_RSPEC=1
            break
        fi
    sleep 10
done

ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper; SF_SUFFIX=${SF_SUFFIX} SF_ROOT=\$(pwd) nosetests -v"
ERROR_TESTS=$?

set +x

get_logs

stop
publish_artifacts
set -x
exit $[ ${ERROR_FATAL} + ${ERROR_RSPEC} + ${ERROR_TESTS} ]
