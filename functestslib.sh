#!/bin/bash

DISABLE_SETX=0

export SF_SUFFIX=${SF_SUFFIX:-tests.dom}
export SKIP_CLEAN_ROLES="y"
export EDEPLOY_ROLES=/var/lib/sf/roles/


case "$(hostname)" in
    "bigger-jenkins")
        JENKINS_URL=46.231.128.203
        ;;
    "faster-jenkins")
        JENKINS_URL=94.143.114.171
        ;;
    "stronger-jenkins")
        JENKINS_URL=46.231.128.54
        ;;
    *)
        JENKINS_URL=$(hostname | sed -e 's/sfstack-//' -e 's/-/./g')
        ;;
esac

[ -z "${JENKINS_URL}" ] && JENKINS_URL="localhost"

GERRIT_PROJECT=${GERRIT_PROJECT-sf}
CURRENT_BRANCH=`git branch | sed -n -e 's/^\* \(.*\)/\1/p'`
# If run outside Jenkins use the current branch name
GERRIT_CHANGE_NUMBER=${GERRIT_CHANGE_NUMBER-$CURRENT_BRANCH}
GERRIT_PATCHSET_NUMBER=${GERRIT_PATCHSET_NUMBER-0}
[ "$USER" = "jenkins" ] && GROUP="www-data" || GROUP="$USER"

ARTIFACTS_RELPATH="logs/${LOG_PATH}"
ARTIFACTS_ROOT="/var/lib/sf/artifacts"
ARTIFACTS_DIR="${ARTIFACTS_ROOT}/${ARTIFACTS_RELPATH}"

function get_ip {
    grep -B 1 "name:[ \t]*$1" /tmp/lxc-conf/sf-lxc.yaml | head -1 | awk '{ print $2 }'
}

function prepare_artifacts {
    [ -d ${ARTIFACTS_DIR} ] && sudo rm -Rf ${ARTIFACTS_DIR}
    sudo mkdir -p ${ARTIFACTS_DIR}
    sudo chown -R $USER:$GROUP ${ARTIFACTS_ROOT}
    sudo chmod -R +w ${ARTIFACTS_ROOT}
    set +x
    if [ ${GROUP} = 'www-data' ]; then
        echo "Logs will be available here: http://${JENKINS_URL}:8081/${ARTIFACTS_RELPATH}"
    else
        echo "Logs will be available here: ${ARTIFACTS_DIR}"
    fi
    set -x
}

function publish_artifacts {
    set +x
    sudo find ${ARTIFACTS_DIR} -type d -exec chmod 550 {} \;
    sudo find ${ARTIFACTS_DIR} -type f -exec chmod 440 {} \;
    sudo chown -R $USER:$GROUP ${ARTIFACTS_DIR}
    if [ ${GROUP} = 'www-data' ]; then
        echo "Logs are available here: http://${JENKINS_URL}:8081/${ARTIFACTS_RELPATH}"
    else
        echo "Logs will be available here: ${ARTIFACTS_DIR}"
    fi
}

function scan_and_configure_knownhosts {
    local ip=`get_ip puppetmaster`
    ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$ip" > /dev/null 2>&1 || echo
    RETRIES=0
    echo " [+] Starting ssh-keyscan on $ip:22"
    while true; do
        KEY=`ssh-keyscan -p 22 $ip 2> /dev/null`
        if [ "$KEY" != ""  ]; then
            ssh-keyscan $ip 2> /dev/null >> "$HOME/.ssh/known_hosts"
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
    #This delay is used to wait a bit before fetching log file from hosts
    #in order to not avoid so important logs that can appears some seconds
    #after a failure.
    sleep 30
    O=${ARTIFACTS_DIR}
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper; ./getlogs.sh"
    scp -r -o StrictHostKeyChecking=no root@`get_ip puppetmaster`:/tmp/logs/* $O/
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
    set +x
    DISABLE_SETX=1
    exec 6>&1                                   # Link file descriptor #6 with stdout.
    exec > ${ARTIFACTS_DIR}/failure-reason.txt  # stdout replaced with file "logfile.txt".

    echo "$(hostname) FAIL to run functionnal tests of this change:"
    display_head

    checkpoint "FAIL: $1"
    host_debug
    checkpoint "host_debug"
    get_logs
    checkpoint "get-logs"
    lxc_stop
    checkpoint "lxc-stop"
    [ -f ${ARTIFACTS_DIR}/sf-bootstrap.log ] && {
            echo "Typical error message ---["
            grep -i 'err:\|could not\|fail\|error' ${ARTIFACTS_DIR}/sf-bootstrap.log | grep -v '^-'
            echo "]---"
    }
    echo -e "\n\n\n====== $1 OUTPUT ======\n"
    case $1 in
        "Roles building FAILED")
            tail -n 120 ${ARTIFACTS_DIR}/build_roles.sh.output
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
    echo -e "\n\n\n====== END OF $1 OUTPUT ======\n"
    publish_artifacts
    checkpoint "publish-artifacts"

    exec 1>&6 6>&-      # Restore stdout and close file descriptor #6.
    echo -e "\n---------------------------------------------------------------------------\n"
    cat ${ARTIFACTS_DIR}/failure-reason.txt
    exit 1
}

function waiting_stack_created {
    while true; do
        heat stack-list | grep -i softwarefactory | grep -i fail
        [ "$?" -eq "0" ] && {
            echo "Stack creation has failed ..."
            # TODO: get the logs (heat stack-show)
            exit 1
        }
        heat stack-list | grep -i softwarefactory | grep -i create_complete
        [ "$?" -eq "0" ] && break
        sleep 60
    done
}

function wait_for_bootstrap_done {
    retries=0
    max_retries=$1
    while true; do
        # We wait for the bootstrap script that run on puppetmaster node finish its work
        ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` test -f puppet-bootstrapper/build/bootstrap.done
        [ "$?" -eq "0" ] && return 0
        ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "echo 'Last lines are: --['; tail -n 3 /var/log/sf-bootstrap.log; echo ']--';"
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
            "cd puppet-bootstrapper; SF_SUFFIX=${SF_SUFFIX} SF_ROOT=\$(pwd) nosetests -v" 2>&1 \
            | tee ${ARTIFACTS_DIR}/functional-tests.output
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
        ./tests/backup_restore/run_provisioner.sh
        # Create a backup
        ./tools/managesf/cli/sf-manage.py --host ${SF_SUFFIX} --auth-server ${SF_SUFFIX} --auth user1:userpass backup_start
        # Fetch the backup
        ./tools/managesf/cli/sf-manage.py --host ${SF_SUFFIX} --auth-server ${SF_SUFFIX} --auth user1:userpass backup_get
        mv sf_backup.tar.gz /tmp
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
        ./tools/managesf/cli/sf-manage.py --host ${SF_SUFFIX} --auth-server ${SF_SUFFIX} --auth user1:userpass restore --filename /tmp/sf_backup.tar.gz
        # Start the checker
        sleep 60
        ./tests/backup_restore/run_checker.sh
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
    echo "$ELAPSED - $* " | sudo tee -a ${ARTIFACTS_DIR}/tests_profiling
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    START=$(date '+%s')
    [ ${DISABLE_SETX} -eq 0 ] && set -x
}
