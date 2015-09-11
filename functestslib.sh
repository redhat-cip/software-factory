#!/bin/bash

DISABLE_SETX=0

export SF_SUFFIX=${SF_SUFFIX:-tests.dom}
export SKIP_CLEAN_ROLES="y"
export EDEPLOY_ROLES=/var/lib/sf/roles/

MANAGESF_URL=http://managesf.${SF_SUFFIX}
hostname | grep -q sfstack && JENKINS_IP=$(hostname | sed -e 's/sfstack-[^-]*-//' -e 's/-/./g') || JENKINS_IP=localhost
JENKINS_URL="http://${JENKINS_IP}:8081/"

GERRIT_PROJECT=${GERRIT_PROJECT-sf}
CURRENT_BRANCH=`git branch | sed -n -e 's/^\* \(.*\)/\1/p'`
# If run outside Jenkins use the current branch name
GERRIT_CHANGE_NUMBER=${GERRIT_CHANGE_NUMBER-$CURRENT_BRANCH}
GERRIT_PATCHSET_NUMBER=${GERRIT_PATCHSET_NUMBER-0}
[ "$USER" = "jenkins" ] && GROUP="www-data" || GROUP="$USER"

ARTIFACTS_RELPATH="logs/${LOG_PATH}"
ARTIFACTS_ROOT="/var/lib/sf/artifacts"
ARTIFACTS_DIR="${ARTIFACTS_ROOT}/${ARTIFACTS_RELPATH}"

CONFDIR=/var/lib/lxc-conf

function clean_old_cache {
    # Remove directory older than 1 week (7 days)
    echo "Removing old item from cache..."
    for item in $(find /var/lib/sf/roles/upstream/* /var/lib/sf/roles/install/* -maxdepth 0 -ctime +7 | \
        grep -v "\(${SF_VER}\|${PREVIOUS_SF_VER}\)"); do
            if [ -f "${item}" ] || [ -d "${item}" ]; then
                echo ${item}
                sudo rm -Rf ${item}
            fi
    done
    echo "Done."
}

function get_ip {
    local p=${CONFDIR}/sf-lxc.yaml
    # This is for compatibility with 0.9.2 version especially for
    # the upgrade test from 0.9.2 to 0.9.3
    # TODO(fbo) remove that when 0.9.3 is tagged
    [ ! -f "$p" ] && p=/tmp/lxc-conf/sf-lxc.yaml
    grep -B 1 "name:[ \t]*$1" $p | head -1 | awk '{ print $2 }'
}

function wait_for_statement {
    local STATEMENT=$1
    local EXPECT_RETURN_CODE=${2-0}
    local MAX_RETRY=${3-40}
    local SLEEP_TIME=${4-5}
    while true; do
        eval "${STATEMENT}" &> /dev/null
        if [ "$?" == "${EXPECT_RETURN_CODE}" ]; then
            break
        fi
        sleep ${SLEEP_TIME}
        let MAX_RETRY=MAX_RETRY-1
        if [ "${MAX_RETRY}" == 0 ]; then
            echo "Following statement didn't happen: [$STATEMENT]"
            return 1
        fi
    done
}

function prepare_artifacts {
    [ -d ${ARTIFACTS_DIR} ] && sudo rm -Rf ${ARTIFACTS_DIR}
    sudo mkdir -p ${ARTIFACTS_DIR}
    sudo chown -R $USER:$GROUP ${ARTIFACTS_ROOT}
    sudo chmod -R 755 ${ARTIFACTS_ROOT}
    set +x
    if [ ${GROUP} = 'www-data' ]; then
        echo "Logs will be available here: ${JENKINS_URL}/${ARTIFACTS_RELPATH}"
    else
        echo "Logs will be available here: ${ARTIFACTS_DIR}"
    fi
    set -x
}

function swift_upload_artifacts {
    # Environment variables HOST, ACCOUNT, CONTAINER and SECRET must be set
    if [ -z "${HOST}" ] || [ -z "${ACCOUNT}" ] || [ -z "${CONTAINER}" ] || [ -z "${SECRET}" ]; then
        return
    fi

    PREFIX=${BUILD_ID:-""}
    if [ "${PREFIX}" == "" ]; then
        PREFIX=`date +"%Y%m%d-%H%M%S"`
    fi

    INDEXFILE=`mktemp`

    echo "<html><body>" > ${INDEXFILE}
    for OBJECT in `find $1 -type f`; do
        SWIFT_PATH="/v1/${ACCOUNT}/${CONTAINER}/${PREFIX}/${OBJECT}"
        TEMPURL=`swift tempurl PUT 3600 ${SWIFT_PATH} ${SECRET}`
        curl -s -H "X-Delete-After: 864000" -H "Content-Type: text/plain" -X PUT --upload-file "$OBJECT" "http://${HOST}${TEMPURL}"
        echo -e "<a href=\"http://${HOST}${SWIFT_PATH}\">${OBJECT}</a><br />\n" >> ${INDEXFILE}
    done
    echo "</body></html>" >> ${INDEXFILE}

    SWIFT_PATH="/v1/${ACCOUNT}/${CONTAINER}/${PREFIX}/index.html"
    TEMPURL=`swift tempurl PUT 3600 ${SWIFT_PATH} ${SECRET}`
    curl -i -H "X-Delete-After: 864000" -X PUT --upload-file ${INDEXFILE} "http://${HOST}${TEMPURL}"

    echo "Artifacts uploaded to Swift: http://${HOST}${SWIFT_PATH}"

    rm ${INDEXFILE}
}

function publish_artifacts {
    set +x
    sudo find ${ARTIFACTS_DIR} -type d -exec chmod 555 {} \;
    sudo find ${ARTIFACTS_DIR} -type f -exec chmod 444 {} \;
    if [ ${GROUP} = 'www-data' ]; then
        echo "Logs are available here: ${JENKINS_URL}/${ARTIFACTS_RELPATH}"
    else
        echo "Logs will be available here: ${ARTIFACTS_DIR}"
    fi
    swift_upload_artifacts ${ARTIFACTS_DIR}
}

function scan_and_configure_knownhosts {
    local ip=`get_ip puppetmaster`
    rm -f "$HOME/.ssh/known_hosts"
    RETRIES=0
    echo " [+] Starting ssh-keyscan on $ip:22"
    while true; do
        KEY=`ssh-keyscan -p 22 $ip`
        if [ "$KEY" != ""  ]; then
            ssh-keyscan $ip | tee -a "$HOME/.ssh/known_hosts"
            echo "  -> $role:22 is up!"
            return 0
        fi
        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && return 1
        echo "  [E] ssh-keyscan on $ip:22 failed, will retry in 20 seconds (attempt $RETRIES/40)"
        sleep 20
    done
}

function get_logs {
    [ "$(get_ip puppetmaster)" == "" ] && return
    #This delay is used to wait a bit before fetching log file from hosts
    #in order to not avoid so important logs that can appears some seconds
    #after a failure.
    sleep 5
    O=${ARTIFACTS_DIR}
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper; ./getlogs.sh"
    scp -r -o StrictHostKeyChecking=no root@`get_ip puppetmaster`:/tmp/logs/* $O/

    # Retrieve Xunit output and store it in Jenkins workspace
    scp -r -o StrictHostKeyChecking=no root@`get_ip puppetmaster`:~/puppet-bootstrapper/nosetests.xml .

    # Retrieve mariadb log
    mkdir -p ${O}/mysql
    scp -r -o StrictHostKeyChecking=no root@`get_ip mysql`:/var/log/mariadb/mariadb.log ${O}/mysql

    for i in gerrit  jenkins  managesf  mysql  puppetmaster  redmine  slave; do
        mkdir -p ${O}/$i/system
        sudo cp -f /var/lib/lxc/$i/rootfs/var/log/{messages,cloud-init*} ${O}/$i/system
    done
}

function host_debug {
    set +x
    sudo dmesg -c > ${ARTIFACTS_DIR}/host_debug_dmesg
    ps aufx >> ${ARTIFACTS_DIR}/host_debug_ps-aufx
    free -m | tee -a ${ARTIFACTS_DIR}/host_debug_free
    sudo df -h | tee -a ${ARTIFACTS_DIR}/host_debug_df
    [ ${DISABLE_SETX} -eq 0 ] && set -x
}

function display_head {
    [ ! -z "${GERRIT_PROJECT}" ] && echo "${GERRIT_PROJECT} - change ${GERRIT_CHANGE_NUMBER} patchset ${GERRIT_PATCHSET_NUMBER}  (${CURRENT_BRANCH})"
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    git log -n 1
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo
}

function pre_fail {
    set -x
    DISABLE_SETX=1
    echo "$(hostname) FAIL to run functionnal tests of this change:"
    display_head

    checkpoint "FAIL: $1"
    host_debug
    checkpoint "host_debug"
    get_logs
    checkpoint "get-logs"
    echo -e "\n\n\n====== $1 OUTPUT ======\n"
    case $1 in
        "Roles building FAILED")
            echo "bad luck..."
            ;;
        "LXC bootstrap FAILED")
            tail -n 120 ${ARTIFACTS_DIR}/lxc-start.output
            ;;
        "Can't SSH")
            more ${ARTIFACTS_DIR}/host_debug*
            ;;
        "Bootstrap did not complete")
            tail -n 120 ${ARTIFACTS_DIR}/sf-bootstrap.log
            ;;
        "Serverspec failed")
            tail -n 10 ${ARTIFACTS_DIR}/sf-bootstrap.log
            cat ${ARTIFACTS_DIR}/serverspec.output
            ;;
        "Functional tests failed")
            tail -n 10 ${ARTIFACTS_DIR}/sf-bootstrap.log
            cat ${ARTIFACTS_DIR}/functional-tests.output
            ;;
    esac
    [ -f ${ARTIFACTS_DIR}/sf-bootstrap.log ] && {
            echo "Typical error message ---["
            grep -A 3 -B 3 -i 'err:\|could not\|fail\|error' ${ARTIFACTS_DIR}/sf-bootstrap.log | grep -v '^-'
            echo "]---"
    }
    echo -e "\n\n\n====== END OF $1 OUTPUT ======\n"
    publish_artifacts
    checkpoint "publish-artifacts"

    exit 1
}

function waiting_stack_created {
    local stackname=$1
    RETRIES=0
    while true; do
        heat stack-list | grep -i $stackname | grep -i fail
        [ "$?" -eq "0" ] && {
            echo "Stack creation has failed ..."
            # TODO: get the logs (heat stack-show)
            heat_stop
            exit 1
        }
        heat stack-list | grep -i $stackname | grep -i create_complete
        [ "$?" -eq "0" ] && break
        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && exit 1
        sleep 60
    done
}

function wait_for_bootstrap_done {
    retries=0
    max_retries=$1
    while true; do
        # We wait for the bootstrap script that run on puppetmaster node finish its work.
        # We avoid password auth here as we can fall in a case that the node responds but the pub key has
        # not been placed by cloudinit and then we stay stuck here.
        lastlines=$(ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey root@`get_ip puppetmaster` "tail -n 3 /var/log/sf-bootstrap.log")
        lret=$?
        if [ $retries -gt 2 ] && [ $lret != 0 ]; then
            # The ssh connection failed more than enough ... so exit !
            return 1
        fi
        echo "---- Last lines are: ----";
        echo $lastlines
        echo "-------------------------";
        # The fail below is more targeted for the HEAT deployment (When the bootstrap script ssh fails to connect to the nodes)
        [ -n "$(echo -n $lastlines | grep 'Permission denied')" ] && return 1
        RET=$(ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey root@`get_ip puppetmaster` cat /root/sf-bootstrap-data/bootstrap.done)
        [ ! -z "${RET}" ] && return ${RET}
        let retries=retries+1
        [ "$retries" == "$max_retries" ] && return 1
        sleep 60
    done
}

function run_serverspec {
    echo "$(date) ======= Starting serverspec tests ========="
    retries=0
    while true; do
        ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper/serverspec/; rake spec" 2>&1 | \
            tee ${ARTIFACTS_DIR}/serverspec.output
        [ "${PIPESTATUS[0]}" -eq "0" ] && return 0
        let retries=retries+1
        [ "$retries" == "5" ] && return 1
        sleep 10
    done
}

function run_functional_tests {
    echo "$(date) ======= Starting functional tests ========="
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` \
            "cd puppet-bootstrapper; nosetests --with-xunit -v" 2>&1 | tee ${ARTIFACTS_DIR}/functional-tests.output
    return ${PIPESTATUS[0]}
}

function run_puppet_allinone_tests {
    echo "$(date) ======= Starting Puppet all in one tests ========="
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` \
            "puppet master --compile allinone --environment=sf" 2>&1 &> ${ARTIFACTS_DIR}/functional-tests.output
    return ${PIPESTATUS[0]}
}



function run_tests {
    r=$1
    scan_and_configure_knownhosts || pre_fail "Can't SSH"
    checkpoint "scan_and_configure_knownhosts"
    wait_for_bootstrap_done $r || pre_fail "Bootstrap did not complete"
    checkpoint "wait_for_bootstrap_done"
    run_serverspec || pre_fail "Serverspec failed"
    checkpoint "run_serverspec"
    run_functional_tests || pre_fail "Functional tests failed"
    checkpoint "run_functional_tests"
    run_puppet_allinone_tests || pre_fail "Puppet all in one tests failed"
    checkpoint "run_puppet_allinone_tests"
}

function run_backup_restore_tests {
    r=$1
    type=$2
    if [ "$type" == "provision" ]; then
        scan_and_configure_knownhosts
        wait_for_bootstrap_done $r || pre_fail "Bootstrap did not complete"
        # Run server spec to be more confident
        run_serverspec || pre_fail "Serverspec failed"
        # Start the provisioner
        ./tools/provisioner_checker/run.sh provisioner
        # Create a backup
        ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "sfmanager --url ${MANAGESF_URL} --auth-server-url ${MANAGESF_URL} --auth user1:userpass backup start"
        sleep 10
        # Fetch the backup
        ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "sfmanager --url ${MANAGESF_URL} --auth-server-url ${MANAGESF_URL} --auth user1:userpass backup get"
        scp -o  StrictHostKeyChecking=no root@`get_ip puppetmaster`:sf_backup.tar.gz /tmp
        # We assume if we cannot move the backup file
        # we need to stop right now
        return $?
    fi
    if [ "$type" == "check" ]; then
        scan_and_configure_knownhosts || pre_fail "Can't SSH"
        wait_for_bootstrap_done $r || pre_fail "Bootstrap did not complete"
        # Run server spec to be more confident
        run_serverspec || pre_fail "Serverspec failed"
        # Restore backup
        scp -o  StrictHostKeyChecking=no /tmp/sf_backup.tar.gz root@`get_ip puppetmaster`:/root/
        ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "sfmanager --url ${MANAGESF_URL} --auth-server-url ${MANAGESF_URL} --auth user1:userpass backup restore --filename sf_backup.tar.gz"
        # Start the checker
        sleep 60
        ./tools/provisioner_checker/run.sh checker
        return $?
    fi
}

function clear_mountpoint {
    # Clean mountpoints
    grep '\/var.*proc' /proc/mounts | awk '{ print $2 }' | while read mountpoint; do
        echo "[+] UMOUNT ${mountpoint}"
        sudo umount ${mountpoint} || echo "umount failed";
    done
    grep '\/var.*lxc' /proc/mounts | awk '{ print $2 }' | while read mountpoint; do
        echo "[+] UMOUNT ${mountpoint}"
        sudo umount ${mountpoint} || echo "umount failed";
    done
}

START=$(date '+%s')

function checkpoint {
    set +x
    NOW=$(date '+%s')
    ELAPSED=$(python -c "print('%03.2fmin' % (($NOW - $START) / 60.0))")
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "$ELAPSED - $* ($(date))" | sudo tee -a ${ARTIFACTS_DIR}/tests_profiling
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    START=$(date '+%s')
    [ ${DISABLE_SETX} -eq 0 ] && set -x
}
