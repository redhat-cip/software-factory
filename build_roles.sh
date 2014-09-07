#!/bin/bash

LOCK="/var/run/sf-build_roles.lock"
if [ -f ${LOCK} ]; then
    echo "Lock file present: ${LOCK}"
    killall make
fi
sudo touch ${LOCK}
trap "sudo rm -f ${LOCK}" 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15

set -e
set -x

. ./role_configrc

#This is updated by an external builder
EDEPLOY_ROLES_SRC_ARCHIVES=root@46.231.128.203:/var/lib/sf/roles/install/edeploy-roles_master

SKIP_CLEAN_ROLES=${SKIP_CLEAN_ROLES:-y}
VIRTUALIZED=""
[ -n "$VIRT" ] && {
    VIRTUALIZED="VIRTUALIZED=params.virt"
}

EDEPLOY_PROJECT=https://github.com/enovance/edeploy.git
EDEPLOY_ROLES_PROJECT=https://github.com/enovance/edeploy-roles.git

CURRENT=`pwd`
SF_ROLES=$CURRENT/edeploy/

BOOTSTRAPPER=$SF_ROLES/puppet_bootstrapper.sh

function build_role {
    ROLE_NAME="$1"
    ROLE_MD5="$2"
    ROLE_FILE="${INST}/${ROLE_NAME}-${SF_REL}"
    UPSTREAM_FILE="${INST}/upstream/${ROLE_NAME}-${SF_REL}"

    if [ ! -f "${ROLE_FILE}.md5" ] || [ "$(cat ${ROLE_FILE}.md5)" != "${ROLE_MD5}" ]; then
        echo "${ROLE_NAME} have been updated"
        # check if upstream is similar
        if [ -f "${UPSTREAM_FILE}.md5" ] && [ "$(cat ${UPSTREAM_FILE}.md5)" == "${ROLE_MD5}" ]; then
            echo "${ROLE_NAME} have already been built upstream, updating local repository"
            sudo cp ${UPSTREAM_FILE}.md5 ${ROLE_FILE}.md5
            sudo tar -xjf ${UPSTREAM_FILE}.edeploy -C ${INST}
        else
            sudo rm -f ${INST}/${ROLE_NAME}.done
            sudo ${MAKE} ${VIRTUALIZED} EDEPLOY_ROLES_PATH=${EDEPLOY_ROLES} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} ${ROLE_NAME}
            echo ${ROLE_MD5} | sudo tee ${ROLE_FILE}.md5
        fi
    else
        echo "${ROLE_NAME} is up-to-date"
    fi
}

if [ ! -d $WORKSPACE ]; then
    sudo mkdir -m 0770 $WORKSPACE
    sudo chown ${USER}:root $WORKSPACE
fi

[ ! -d "$BUILD_DIR" ] && sudo mkdir -p $BUILD_DIR
[ ! -d "${INST}/upstream" ] && sudo mkdir -p ${INST}/upstream

if [ "$SKIP_CLEAN_ROLES" != "y" ]; then
    [ -d "$BUILD_DIR/install" ] && sudo rm -Rf $BUILD_DIR/install
fi
[ ! -d "$CLONES_DIR" ] && sudo mkdir -p $CLONES_DIR
sudo chown -R ${USER} ${CLONES_DIR}

if [ ! -d "${EDEPLOY}" ]; then
    git clone $EDEPLOY_PROJECT ${EDEPLOY}
fi

if [ ! -d "${EDEPLOY_ROLES}" ]; then
    git clone $EDEPLOY_ROLES_PROJECT ${EDEPLOY_ROLES}
fi
EDEPLOY_ROLES_REL=$(cd ${EDEPLOY_ROLES}; ${MAKE} version)

# Prepare prebuild roles
PREBUILD_TARGET=$WORKSPACE/roles/install/$EDEPLOY_ROLES_REL
[ ! -d $PREBUILD_TARGET ] && {
    sudo mkdir -p $PREBUILD_TARGET
    sudo chown ${USER}:root $PREBUILD_TARGET
}
cloud_img="cloud-$EDEPLOY_ROLES_REL.edeploy"
install_server_img="install-server-$EDEPLOY_ROLES_REL.edeploy"

# Check if role synced recently (< 1h)
TIME_DIFF=$(echo $(date '+%s') - 0$(stat -c '%Y' $PREBUILD_TARGET/$install_server_img.md5 2> /dev/null) | bc)
if [ ${TIME_DIFF} -gt 3600 ]; then
    (cd ${EDEPLOY};       git checkout $ED_TAG; git pull)
    (cd ${EDEPLOY_ROLES}; git checkout $ED_TAG; git pull)

    if [ ${EDEPLOY_ROLES_REL} != "$(cd ${EDEPLOY_ROLES}; ${MAKE} version)" ]; then
        echo "============================================================================"
        echo "Edeploy roles version bump from ${EDEPLOY_ROLES_REL} to $(cd ${EDEPLOY_ROLES}; ${MAKE} version)..."
        echo "============================================================================"
        exec ./build_roles.sh
    fi
    TEMP_DIR=$(mktemp -d /tmp/edeploy-check-XXXXX)
    curl -s -o ${TEMP_DIR}/$install_server_img.md5 ${BASE_URL}/$install_server_img.md5
    curl -s -o ${TEMP_DIR}/$cloud_img.md5 ${BASE_URL}/$cloud_img.md5
    [ ! -f $PREBUILD_TARGET/$install_server_img.md5 ] && sudo touch $PREBUILD_TARGET/$install_server_img.md5
    diff $PREBUILD_TARGET/$install_server_img.md5 ${TEMP_DIR}/$install_server_img.md5 || {
        curl -s -o ${TEMP_DIR}/$install_server_img ${BASE_URL}/$install_server_img
        mv ${TEMP_DIR}/$install_server_img* $PREBUILD_TARGET
        # Remove the previously unziped archive
        [ -d $PREBUILD_TARGET/install-server ] && sudo rm -Rf $PREBUILD_TARGET/install-server
    }
    [ ! -f $PREBUILD_TARGET/$cloud_img.md5 ] && sudo touch $PREBUILD_TARGET/$cloud_img.md5
    diff $PREBUILD_TARGET/$cloud_img.md5 ${TEMP_DIR}/$cloud_img.md5 || {
        curl -s -o ${TEMP_DIR}/$cloud_img ${BASE_URL}/$cloud_img
        mv ${TEMP_DIR}/$cloud_img* $PREBUILD_TARGET
        # Remove the previously unziped archive
        [ -d $PREBUILD_TARGET/cloud ] && sudo rm -Rf $PREBUILD_TARGET/cloud
    }
    for role in mysql slave install-server-vm softwarefactory; do
        role=${role}-${SF_REL}
        curl -s -o ${TEMP_DIR}/${role}.md5 ${BASE_URL}/${role}.md5 || continue
        # Swift does not return 404 but 'Not Found'
        grep -q 'Not Found' ${TEMP_DIR}/${role}.md5 && continue
        diff ${TEMP_DIR}/${role}.md5 ${INST}/upstream/${role}.md5 || {
            sudo curl -s -o ${INST}/upstream/${role}.edeploy ${BASE_URL}/${role}.edeploy
            sudo curl -s -o ${INST}/upstream/${role}.edeploy.md5 ${BASE_URL}/${role}.edeploy.md5
            sudo mv ${TEMP_DIR}/${role}.md5 ${INST}/upstream/${role}.md5
            role_md5=$(cat ${INST}/upstream/${role}.edeploy | md5sum - | cut -d ' ' -f1)
            [ "${role_md5}" != "$(cat ${INST}/upstream/${role}.edeploy.md5 | cut -d ' ' -f1)" ] && {
                echo "${role} archive md5 mismatch ! exit."
                exit 1
            }
        }
    done
    rm -Rf ${TEMP_DIR}


    # Verified the prebuild role we have with the md5
    install_server_md5=$(cat $PREBUILD_TARGET/$install_server_img | md5sum - | cut -d ' ' -f1)
    [ "$install_server_md5" != "$(cat $PREBUILD_TARGET/$install_server_img.md5 | cut -d ' ' -f1)" ] && {
        echo "Install server role archive md5 mismatch ! exit."
        exit 1
    }
    cloud_md5=$(cat $PREBUILD_TARGET/$cloud_img | md5sum - | cut -d ' ' -f1)
    [ "$cloud_md5" != "$(cat $PREBUILD_TARGET/$cloud_img.md5 | cut -d ' ' -f1)" ] && {
        echo "cloud role archive md5 mismatch ! exit."
        exit 1
    }
    sudo touch $PREBUILD_TARGET/$install_server_img.md5
fi

# Uncompress prebuild images if needed
cd $PREBUILD_TARGET
[ ! -d cloud ] && {
    mkdir cloud
    sudo tar -xzf $cloud_img -C cloud
    touch cloud.done
}
[ ! -d install-server ] && {
    mkdir install-server
    sudo tar -xzf $install_server_img -C install-server
    touch install-server.done
}
cd -

cd $SF_ROLES
[ ! -d "$BUILD_DIR/install/${DVER}-${SF_REL}" ] && sudo mkdir -p $BUILD_DIR/install/${DVER}-${SF_REL}

build_role "mysql" $(cat mysql.install | md5sum | awk '{ print $1}')
ME=$?
build_role "slave" $(cat slave.install | md5sum | awk '{ print $1}')
SE=$?
build_role "softwarefactory"   $(cd ..; find ${SF_DEPS} -type f | sort | grep -v '\.tox' | xargs cat | md5sum | awk '{ print $1}')
SFE=$?
build_role "install-server-vm" $(cd ..; find ${IS_DEPS} -type f | sort | grep -v '\.tox' | xargs cat | md5sum | awk '{ print $1}')
IE=$?

exit $[ $ME + $SE + $SFE + $IE ];
