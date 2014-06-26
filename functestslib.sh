ERROR_FATAL=0
ERROR_RSPEC=0
ERROR_TESTS=0

export SF_SUFFIX=${SF_SUFFIX:-tests.dom}
export SKIP_CLEAN_ROLES="y"
export EDEPLOY_ROLES=/var/lib/sf/roles/

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
    sudo chmod -R +w ${ARTIFACTS_ROOT}
    if [ ${GROUP} = 'www-data' ]; then
        echo "Logs will be available here: http://${JENKINS_URL}:8081/${ARTIFACTS_RELPATH}"
    else
        echo "Logs will be available here: ${ARTIFACTS_DIR}"
    fi
}

function publish_artifacts {
    find ${ARTIFACTS_DIR} -type d -exec chmod 550 {} \;
    find ${ARTIFACTS_DIR} -type f -exec chmod 440 {} \;
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
            break
        fi
        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && break
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


function pre_fail {
    set +x
    echo $1
    stop &> /dev/null
    echo -e "\n\n\n====== EDEPLOY BUILD OUTPUT ======\n"
    tail -n 120 ${ARTIFACTS_DIR}/build_roles.sh.output
    echo -e "\n\n\n====== END OF EDEPLOY BUILD OUTPUT ======\n"
    publish_artifacts
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
        [ "$?" -eq "0" ] && break
        let retries=retries+1
        if [ "$retries" == "$max_retries" ]; then
            ERROR_FATAL=1
            break
        fi
        sleep 60
    done
}

function run_serverspec {
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
}

function run_functional_tests {
    ssh -o StrictHostKeyChecking=no root@`get_ip puppetmaster` "cd puppet-bootstrapper; SF_SUFFIX=${SF_SUFFIX} SF_ROOT=\$(pwd) nosetests -v"
    ERROR_TESTS=$?
}

function run_tests {
    r=$1
    scan_and_configure_knownhosts
    wait_for_bootstrap_done $r
    run_serverspec
    [ "$ERROR_RSPEC" != "0" ] && return
    run_functional_tests
    [ "$ERROR_TESTS" != "0" ] && return
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
