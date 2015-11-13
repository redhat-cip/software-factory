#!/bin/bash

DISABLE_SETX=0
[ -z "${DEBUG}" ] && DISABLE_SETX=1 || set -x

export SF_HOST=${SF_HOST:-tests.dom}
export SKIP_CLEAN_ROLES="y"

MANAGESF_URL=https://${SF_HOST}
ADMIN_USER=admin
ADMIN_PASSWORD=userpass
JENKINS_URL="http://${SF_HOST:-tests.dom}/jenkinslogs/${JENKINS_IP}:8081/"

ARTIFACTS_DIR="/var/lib/sf/artifacts"
# This environment variable is set ZUUL in the jenkins job workspace
# The artifacts directory is then at the root of workspace
[ -n "$SWIFT_artifacts_URL" ] && ARTIFACTS_DIR="$(pwd)/../artifacts"

CONFDIR=/var/lib/lxc-conf

function prepare_artifacts {
    [ -d ${ARTIFACTS_DIR} ] && sudo rm -Rf ${ARTIFACTS_DIR}
    sudo mkdir -p ${ARTIFACTS_DIR}
    USER=$(whoami)
    sudo chown -R $USER:$USER ${ARTIFACTS_DIR}
    sudo chmod -R 755 ${ARTIFACTS_DIR}
    set +x
    if [ -n ${SWIFT_artifacts_URL} ]; then
        echo "Logs will be available here: $SWIFT_artifacts_URL"
    else
        echo "Logs will be available here: ${ARTIFACTS_DIR}"
    fi
    set -x
}

function lxc_stop {
    (cd deploy/lxc; sudo ./deploy.py --workspace ${SF_WORKSPACE} stop)
    checkpoint "lxc-stop"
}

function lxc_init {
    ver=${1:-${SF_VER}}
    (cd deploy/lxc; sudo ./deploy.py init --workspace ${SF_WORKSPACE} --refarch $REFARCH --version ${ver}) || fail "LXC start FAILED"
    checkpoint "lxc-start"
}

function lxc_start {
    (cd deploy/lxc; sudo ./deploy.py start --workspace ${SF_WORKSPACE} --refarch $REFARCH) || fail "LXC start FAILED"
    checkpoint "lxc-start"
}

function build_image {
    # Make sure subproject are available
    if [ ! -d "${CAUTH_CLONED_PATH}" ] || [ ! -d "${MANAGESF_CLONED_PATH}" ] || [ ! -d "${PYSFLIB_CLONED_PATH}" ]; then
        ./image/fetch_subprojects.sh
    fi
    if [ -z "${SKIP_BUILD}" ]; then
        # Retry to build role if it fails before exiting
        ./build_image.sh ${ARTIFACTS_DIR} || ./build_image.sh ${ARTIFACTS_DIR} || fail "Roles building FAILED"
        checkpoint "build_image"
        prepare_functional_tests_venv
    else
        echo "SKIP_BUILD: Reusing previously built image, just update source code without re-installing"
        echo "            To update requirements and do a full installation, do not use SKIP_BUILD"
        set -e
        sudo rsync -a --delete puppet/manifests/ ${IMAGE_PATH}/etc/puppet/environments/sf/manifests/
        sudo rsync -a --delete puppet/modules/ ${IMAGE_PATH}/etc/puppet/environments/sf/modules/
        sudo rsync -a --delete puppet/hiera/ ${IMAGE_PATH}/etc/puppet/hiera/sf/
        sudo cp -Rv config/scripts/* ${IMAGE_PATH}/usr/local/bin/
        sudo cp -Rv config/defaults/* ${IMAGE_PATH}/etc/puppet/hiera/sf/
        echo "SKIP_BUILD: direct copy of ${MANAGESF_CLONED_PATH}/ to ${IMAGE_PATH}/var/www/managesf/"
        sudo rsync -a --delete ${MANAGESF_CLONED_PATH}/ ${IMAGE_PATH}/var/www/managesf/
        echo "SKIP_BUILD: direct copy of ${CAUTH_CLONED_PATH}/ to ${IMAGE_PATH}/var/www/cauth/"
        sudo rsync -a --delete ${CAUTH_CLONED_PATH}/ ${IMAGE_PATH}/var/www/cauth/
        PYSFLIB_LOC=${IMAGE_PATH}/$(sudo chroot ${IMAGE_PATH} pip show pysflib | grep '^Location:' | awk '{ print $2 }')
        echo "SKIP_BUILD: direct copy of ${PYSFLIB_CLONED_PATH}/pysflib/ to ${PYSFLIB_LOC}/pysflib/"
        sudo rsync -a --delete ${PYSFLIB_CLONED_PATH}/pysflib/ ${PYSFLIB_LOC}/pysflib/
        sudo cp image/edeploy ${IMAGE_PATH}/usr/sbin/edeploy
        set +e
    fi
}

function configure_network {
    if [ "${SF_HOST}" != "tests.dom" ]; then
        echo "${SF_HOST} must have ssh key authentitcation and use root user by default"
        return
    fi
    local ip=192.168.135.101
    rm -f "$HOME/.ssh/known_hosts"
    RETRIES=0
    echo " [+] Starting ssh-keyscan on $ip:22"
    while [ $RETRIES -lt 40 ]; do
        KEY=`ssh-keyscan -p 22 $ip 2> /dev/null`
        if [ "$KEY" != ""  ]; then
            echo $KEY > "$HOME/.ssh/known_hosts"
            echo "  -> $ip:22 is up!"
            break
        fi
        let RETRIES=RETRIES+1
        echo "  [E] ssh-keyscan on $ip:22 failed, will retry in 1 seconds (attempt $RETRIES/40)"
        sleep 1
    done
    [ $RETRIES -eq 40 ] && fail "Can't connect to $ip"
    echo "[+] Avoid ssh error"
    cat << EOF > ~/.ssh/config
Host ${SF_HOST}
    Hostname 192.168.135.101
    User root
EOF
    chmod 0600 ~/.ssh/config

    echo "[+] Adds ${SF_HOST} to /etc/hosts"
    reset_etc_hosts_dns "${SF_HOST}" 192.168.135.101
    checkpoint "configure_network"
}

function get_logs {
    #This delay is used to wait a bit before fetching log file from hosts
    #in order to not avoid so important logs that can appears some seconds
    #after a failure.
    set +e
    sleep 5
    (
    sudo cp ${IMAGE_PATH}.{rpm,pip} ${ARTIFACTS_DIR}/
    sudo cp /var/lib/lxc/managesf/rootfs/var/log/messages ${ARTIFACTS_DIR}/
    sudo cp /var/lib/lxc/managesf/rootfs/var/log/upgrade-bootstrap.log ${ARTIFACTS_DIR}/
    sudo cp /var/lib/lxc/managesf/rootfs/var/log/cloud-init* ${ARTIFACTS_DIR}/
    sudo cp -r /var/lib/lxc/managesf/rootfs/home/gerrit/site_path/logs/ ${ARTIFACTS_DIR}/gerrit/
    sudo cp -r /var/lib/lxc/managesf/rootfs/usr/share/redmine/log/ ${ARTIFACTS_DIR}/redmine/
    sudo cp -r /var/lib/lxc/managesf/rootfs/var/log/managesf/ ${ARTIFACTS_DIR}/managesf/
    sudo cp -r /var/lib/lxc/managesf/rootfs/var/log/cauth/ ${ARTIFACTS_DIR}/cauth/
    sudo cp -r /var/lib/lxc/managesf/rootfs/var/log/httpd/ ${ARTIFACTS_DIR}/httpd/
    sudo cp -r /var/lib/lxc/managesf/rootfs/var/log/zuul/ ${ARTIFACTS_DIR}/zuul/
    sudo cp -r /var/lib/lxc/managesf/rootfs/var/log/nodepool/ ${ARTIFACTS_DIR}/nodepool/
    sudo cp -r /var/lib/lxc/managesf/rootfs/var/lib/jenkins/jobs/ ${ARTIFACTS_DIR}/jenkins-jobs/
    sudo cp -r /var/lib/lxc/managesf/rootfs/root/config/ ${ARTIFACTS_DIR}/config-project
    sudo cp -r /var/lib/lxc/managesf/rootfs/etc/puppet/hiera/sf/ ${ARTIFACTS_DIR}/hiera
    sudo cp -r /var/lib/lxc/managesf/rootfs/root/sf-bootstrap-data/hiera/ ${ARTIFACTS_DIR}/sf-bootstrap-data-hiera
    ) 2> /dev/null
    sudo chown -R ${USER} ${ARTIFACTS_DIR}
    checkpoint "get_logs"
}

function host_debug {
    set +x
    mkdir ${ARTIFACTS_DIR}/host_debug
    sudo dmesg -c > ${ARTIFACTS_DIR}/host_debug/dmesg
    ps aufx >> ${ARTIFACTS_DIR}/host_debug/ps-aufx
    free -m | tee -a ${ARTIFACTS_DIR}/host_debug/free
    sudo df -h | tee -a ${ARTIFACTS_DIR}/host_debug/df
    cat /etc/hosts > ${ARTIFACTS_DIR}/host_debug/hosts
    checkpoint "host_debug"
    [ ${DISABLE_SETX} -eq 0 ] && set -x
}

function display_head {
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    git log -n 1
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo
}

function fail {
    set +x
    msg=$1
    log_file=$2
    DISABLE_SETX=1
    echo -e "\n\n-----8<-------8<------\n  END OF TEST, FAIL: "
    if [ ! -z "$log_file" ] && [ -f "$log_file" ]; then
        echo "=> Log file $log_file --["
        tail -n 500 $log_file
        echo "]--"
    fi
    display_head

    checkpoint "FAIL: $msg"
    host_debug
    [ -z "$SWIFT_artifacts_URL" ] && {
        get_logs
    }
    echo "$0 ${REFARCH} ${TEST_TYPE}: FAILED"
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

function run_bootstraps {
    configure_network
    eval $(ssh-agent)
    ssh-add ~/.ssh/id_rsa
    echo "$(date) ======= run_bootstraps" | tee -a ${ARTIFACTS_DIR}/bootstraps.log
    [ "${REFARCH}" = "2nodes-jenkins" ] && OPTIONS="-i 192.168.135.102"
    ssh -A -tt ${SF_HOST} sfconfig.sh -a ${REFARCH} ${OPTIONS} 2>&1 | tee ${ARTIFACTS_DIR}/bootstraps.log | grep '\(Info:\|Warning:\|Error:\|\[sfconfig\]\)'
    res=${PIPESTATUS[0]}
    kill -9 $SSH_AGENT_PID
    [ "$res" != "0" ] && fail "Bootstrap fails" ${ARTIFACTS_DIR}/bootstraps.log
    echo "[+] Fetch ${SF_HOST} ssl cert"
    scp -r ${SF_HOST}:/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt /var/lib/sf/venv/lib/python2.7/site-packages/requests/cacert.pem
    cp /var/lib/sf/venv/lib/python2.7/site-packages/requests/cacert.pem /var/lib/sf/venv/lib/python2.7/site-packages/pip/_vendor/requests/cacert.pem

    echo "[+] Fetch bootstrap data"
    rm -Rf sf-bootstrap-data
    scp -r ${SF_HOST}:sf-bootstrap-data .
    checkpoint "run_bootstraps"
}

function prepare_functional_tests_venv {
    echo "$(date) ======= Prepare functional tests venv ======="
    if [ ! -d /var/lib/sf/venv ]; then
        sudo virtualenv /var/lib/sf/venv
        sudo chown -R ${USER} /var/lib/sf/venv
    fi
    (
        . /var/lib/sf/venv/bin/activate
        pip install --upgrade pip
        pip install 'requests[security]'
        pip install -r ${PYSFLIB_CLONED_PATH}/requirements.txt
        sed -i '/pysflib/d' ${MANAGESF_CLONED_PATH}/requirements.txt
        pip install -r ${MANAGESF_CLONED_PATH}/requirements.txt
        pip install --upgrade setuptools pbr pycrypto
        pip install pyOpenSSL ndg-httpsclient pyasn1 nose git-review
        cd ${PYSFLIB_CLONED_PATH}; python setup.py install
        cd ${MANAGESF_CLONED_PATH}; python setup.py install
    ) > ${ARTIFACTS_DIR}/venv_prepartion.output
    checkpoint "prepare_venv"
}

function reset_etc_hosts_dns {
    (
        set -x
        host=$1
        ip=$2
        grep -q " ${host}" /etc/hosts || {
            # adds to /etc/hosts if not already defined
            echo "${ip} ${host}" | sudo tee -a /etc/hosts
        } && {
            # else sed in-place
            sudo sed -i "s/^.* ${host}/${ip} ${host}/" /etc/hosts
        }
    ) &> ${ARTIFACTS_DIR}/etc_hosts.log
}

function run_provisioner {
    echo "$(date) ======= run_provisioner"
    . /var/lib/sf/venv/bin/activate
    ./tests/functional/provisioner/provisioner.py 2>> ${ARTIFACTS_DIR}/provisioner.debug || fail "Provisioner failed" ${ARTIFACTS_DIR}/provisioner.debug
    deactivate
    checkpoint "run_provisioner"
}

function run_backup_start {
    echo "$(date) ======= run_backup_start"
    . /var/lib/sf/venv/bin/activate
    sfmanager --url "${MANAGESF_URL}" --auth ${ADMIN_USER}:${ADMIN_PASSWORD} system backup_start || fail "Backup failed"
    sfmanager --url "${MANAGESF_URL}" --auth ${ADMIN_USER}:${ADMIN_PASSWORD} system backup_get   || fail "Backup get failed"
    deactivate
    sudo cp /var/lib/lxc/managesf/rootfs/var/log/managesf/managesf.log ${ARTIFACTS_DIR}/backup_managesf.log
    tar tzvf sf_backup.tar.gz > ${ARTIFACTS_DIR}/backup_content.log
    grep -q '\.bup\/objects\/pack\/.*.pack$' ${ARTIFACTS_DIR}/backup_content.log || fail "Backup empty" ${ARTIFACTS_DIR}/backup_content.log
    checkpoint "run_backup_start"
}

function run_backup_restore {
    echo "$(date) ======= run_backup_restore"
    . /var/lib/sf/venv/bin/activate
    sfmanager --url "${MANAGESF_URL}" --auth ${ADMIN_USER}:${ADMIN_PASSWORD} system restore --filename $(pwd)/sf_backup.tar.gz || fail "Backup resore failed"
    echo "[+] Waiting for gerrit to restart..."
    retry=0
    while [ $retry -lt 1000 ]; do
        wget --spider  http://tests.dom/r/ 2> /dev/null && break
        sleep 1
        let retry=retry+1
    done
    [ $retry -eq 1000 ] && fail "Gerrit did not restart"
    echo "=> Took ${retry} retries"
    # Give it some more time...
    sleep 5
    deactivate
    checkpoint "run_backup_restore"
}

function run_upgrade {
    echo "$(date) ======= run_upgrade"
    sudo git clone file://$(pwd) /var/lib/lxc/managesf/rootfs/root/software-factory  --depth 1 || fail "Could not clone sf in managesf instance"
    echo "[+] Copying new version (${IMAGE_PATH}/ -> /var/lib/lxc/managesf/rootfs/${IMAGE_PATH})"
    sudo mkdir -p /var/lib/lxc/managesf/rootfs/${IMAGE_PATH}/ || fail "Could not copy ${SF_VER}"
    sudo rsync -a --delete ${IMAGE_PATH}/ /var/lib/lxc/managesf/rootfs/${IMAGE_PATH}/ || fail "Could not copy ${SF_VER}"
    echo "[+] Running upgrade"
    ssh ${SF_HOST} "cd software-factory; ./upgrade.sh ${REFARCH}" || fail "Upgrade failed" "/var/lib/lxc/managesf/rootfs/var/log/upgrade-bootstrap.log"
    checkpoint "run_upgrade"
}

function run_checker {
    echo "$(date) ======= run_checker"
    . /var/lib/sf/venv/bin/activate
    ./tests/functional/provisioner/checker.py 2>> ${ARTIFACTS_DIR}/checker.debug || fail "Backup checker failed" ${ARTIFACTS_DIR}/checker.debug
    deactivate
    checkpoint "run_checker"
}

function run_functional_tests {
    echo "$(date) ======= run_functional_tests"
    . /var/lib/sf/venv/bin/activate
    nosetests --with-xunit -v tests/functional > ${ARTIFACTS_DIR}/functional-tests.debug || fail "Functional tests failed" ${ARTIFACTS_DIR}/functional-tests.debug
    deactivate
    checkpoint "run_functional_tests"
}

function run_serverspec_tests {
    echo "$(date) ======= run_serverspec_tests"
    # Wait a few seconds for zuul to start
    sleep 5
    # Copy current serverspec
    sudo rsync -a --delete serverspec/ ${IMAGE_PATH}/etc/serverspec/
    ssh ${SF_HOST} "cd /etc/serverspec; rake spec" 2>&1 | tee ${ARTIFACTS_DIR}/serverspec.output
    [ "${PIPESTATUS[0]}" != "0" ] && fail "Serverspec tests failed"
    checkpoint "run_serverspec_tests"
}

START=$(date '+%s')

function checkpoint {
    set +x
    NOW=$(date '+%s')
    ELAPSED=$(python -c "print('%03.2fmin' % (($NOW - $START) / 60.0))")
    echo
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "$ELAPSED - $* ($(date))" | sudo tee -a ${ARTIFACTS_DIR}/tests_profiling
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    START=$(date '+%s')
    [ ${DISABLE_SETX} -eq 0 ] && set -x
}
