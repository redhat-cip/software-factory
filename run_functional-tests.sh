#!/bin/bash

# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script will build if needed the roles for software-factory
# Then will start the SF in LXC containers
# Then will run the serverspecs and functional tests

if [ "$(id -un)" == "root" ]; then
    echo "Can't run tests as root, use centos user instead"
    exit 1
fi

source functestslib.sh
. role_configrc
bash ./rpm-test-requirements.sh

TEST_TYPE="${1:-functional}"

# Backward compatibility with jjb jobs
[ ${TEST_TYPE} == "1node-allinone" ] && TEST_TYPE=$2

REFARCH_FILE=${SF_ARCH:-$(pwd)/config/refarch/allinone.yaml}

SF_TESTS=${SF_TESTS:-tests/functional}

if [ ${TEST_TYPE} == "openstack" ] && [ ! -n "${OS_AUTH_URL}" ]; then
    echo "Source openrc first"
    exit 1
fi

###############
# Preparation #
###############
echo "Running functional-tests with this HEAD"
display_head
prepare_artifacts
checkpoint "Running tests on $(hostname)"

if [ ${TEST_TYPE} == "openstack" ]; then
    export BUILD_QCOW=1
    which ansible-playbook &> /dev/null || sudo pip install ansible
    heat stack-delete -y sf_stack &> /dev/null
    clean_nodepool_tenant
else
    lxc_stop
fi

[ -z "${KEEP_GLANCE_IMAGE}" ] && build_image

# nosetests should run without a proxy, otherwise REST APIs on the LXC env might
# not be accessible
unset http_proxy
unset https_proxy

TECH_PREVIEW="elasticsearch job-logs-gearman-client job-logs-gearman-worker logstash kibana mirror"
TECH_PREVIEW+=" storyboard storyboard-webclient repoxplorer"

case "${TEST_TYPE}" in
    "minimal")
        # Add tech preview components until they are fully integrated in the refarch
        enable_arch_components locally $REFARCH_FILE "$TECH_PREVIEW"
        lxc_init
        run_bootstraps
        run_serverspec_tests
        ;;
    "functional")
        # Add tech preview components until they are fully integrated in the refarch
        enable_arch_components locally $REFARCH_FILE "$TECH_PREVIEW"
        lxc_init
        run_bootstraps
        run_serverspec_tests
        run_health_base
        lxc_poweroff
        lxc_start
        wait_boot_finished
        run_functional_tests
        if [ "${SF_TESTS}" != "tests/functional" ]; then
            exit 0
        fi
        run_provisioner
        run_backup_start
        lxc_stop
        lxc_init
        run_bootstraps
        run_backup_restore
        run_checker
        change_fqdn
        run_sfconfig
        run_serverspec_tests
        ;;
    "upgrade")
        ./fetch_image.sh ${SF_PREVIOUS_VER} || fail "Could not fetch ${SF_PREVIOUS_VER}"
        # Use previous default arch file
        export REFARCH_FILE=/var/lib/sf/roles/install/${SF_PREVIOUS_VER}/softwarefactory/usr/local/share/sf-default-config/arch.yaml
        lxc_init ${SF_PREVIOUS_VER}
        run_bootstraps
        run_provisioner
        # Add tech preview components until they are fully integrated in the refarch
        enable_arch_components remote /etc/puppet/hiera/sf/arch.yaml "$TECH_PREVIEW"
        run_upgrade
        run_checker "checksum_warn_only"
        run_serverspec_tests
        run_functional_tests
        ;;
    "openstack")
        heat_stop
        heat_init
        heat_wait
        run_heat_bootstraps
        #run_functional_tests  # disabled because it takes too long
        run_health_openstack
        run_it_openstack
        ;;
    "gui")
        lxc_init
        run_bootstraps
        d=$DISPLAY
        pre_gui_tests
        run_gui_test guiTests tests/gui
        failed=$?
        post_gui_tests
        DISPLAY=$d
        if_gui_tests_failure $failed
        ;;
    "video_docs")
        . tests/gui/user_stories/user_stories
        lxc_init
        run_bootstraps
        d=$DISPLAY
        pre_gui_tests
        failed=0
        for video_path in ${!user_stories[@]}; do
            run_gui_test $video_path ${user_stories["$video_path"]}
            a=$?
            if [[ $a > $failed ]]; then
                failed=$a
            fi
            # wait for tmux to be discarded
            sleep 5
        done
        post_gui_tests
        DISPLAY=$d
        if_gui_tests_failure $failed
        ;;
    *)
        echo "[+] Unknown test type ${TEST_TYPE}"
        exit 1
        ;;
esac

DISABLE_SETX=1
checkpoint "end_tests"
# If run locally (outside of zuul) fetch logs/artifacts. If run
# through Zuul then a publisher will be used
[ -z "$SWIFT_artifacts_URL" ] && get_logs
echo "$0 ${REFARCH} ${TEST_TYPE}: SUCCESS"
exit 0;
