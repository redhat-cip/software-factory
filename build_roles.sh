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
    ROLE_FILE="${INST}/${ROLE_NAME}-${SF_VER}"
    UPSTREAM_FILE="${UPSTREAM}/${ROLE_NAME}-${SF_VER}"

    # Make sure role tree is not mounted
    grep -q "${SF_VER}\/${ROLE_NAME}\/proc" /proc/mounts && {
        while true; do
            sudo umount ${INST}/${ROLE_NAME}/proc || break
        done
    }
    if [ ! -f "${ROLE_FILE}.md5" ] || [ "$(cat ${ROLE_FILE}.md5)" != "${ROLE_MD5}" ]; then
        echo "${ROLE_NAME} have been updated"
        # check if upstream is similar
        if [ -f "${UPSTREAM_FILE}.md5" ] && [ "$(cat ${UPSTREAM_FILE}.md5)" == "${ROLE_MD5}" ]; then
            echo "${ROLE_NAME} have already been built upstream, updating local repository"
            sudo rm -Rf ${INST}/${ROLE_NAME}
            sudo mkdir ${INST}/${ROLE_NAME}
            sudo tar -xzf ${UPSTREAM_FILE}.edeploy -C "${INST}/${ROLE_NAME}"
            sudo touch ${INST}/${ROLE_NAME}.done
        else
            sudo rm -f ${INST}/${ROLE_NAME}.done
            sudo ${MAKE} ${VIRTUALIZED} EDEPLOY_ROLES_PATH=${EDEPLOY_ROLES} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} ${ROLE_NAME}
        fi
        echo ${ROLE_MD5} | sudo tee ${ROLE_FILE}.md5
    else
        echo "${ROLE_NAME} is up-to-date"
    fi
}

if [ ! -d $WORKSPACE ]; then
    sudo mkdir -m 0770 $WORKSPACE
    sudo chown ${USER}:root $WORKSPACE
fi

[ ! -d "$BUILD_DIR" ] && sudo mkdir -p $BUILD_DIR
[ ! -d "$UPSTREAM" ] && sudo mkdir -p $UPSTREAM

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

(cd ${EDEPLOY};       git checkout $ED_TAG; git pull)
(cd ${EDEPLOY_ROLES}; git checkout $ED_TAG; git pull)
EDEPLOY_ROLES_REL=$(cd ${EDEPLOY_ROLES}; ${MAKE} version)

# Prepare prebuild roles
PREBUILD_TARGET=$WORKSPACE/roles/install/$EDEPLOY_ROLES_REL
[ ! -d $PREBUILD_TARGET ] && {
    sudo mkdir -p $PREBUILD_TARGET
    sudo chown ${USER}:root $PREBUILD_TARGET
}
cloud_img="cloud-$EDEPLOY_ROLES_REL.edeploy"
install_server_img="install-server-$EDEPLOY_ROLES_REL.edeploy"

# Check if edeploy roles are up-to-date
[ ! -f $PREBUILD_TARGET/$install_server_img.md5 ] && sudo touch $PREBUILD_TARGET/$install_server_img.md5
[ ! -f $PREBUILD_TARGET/$cloud_img.md5 ] &&          sudo touch $PREBUILD_TARGET/$cloud_img.md5
TEMP_DIR=$(mktemp -d /tmp/edeploy-check-XXXXX)
curl -s -o ${TEMP_DIR}/$install_server_img.md5 ${BASE_URL}/$install_server_img.md5
curl -s -o ${TEMP_DIR}/$cloud_img.md5          ${BASE_URL}/$cloud_img.md5
diff $PREBUILD_TARGET/$install_server_img.md5 ${TEMP_DIR}/$install_server_img.md5 || {
    curl -s -o ${TEMP_DIR}/$install_server_img ${BASE_URL}/$install_server_img
    sudo mv -f ${TEMP_DIR}/$install_server_img* $PREBUILD_TARGET
    # Remove the previously unziped archive
    [ -d $PREBUILD_TARGET/install-server ] && sudo rm -Rf $PREBUILD_TARGET/install-server
}
diff $PREBUILD_TARGET/$cloud_img.md5 ${TEMP_DIR}/$cloud_img.md5 || {
    curl -s -o ${TEMP_DIR}/$cloud_img ${BASE_URL}/$cloud_img
    sudo mv -f ${TEMP_DIR}/$cloud_img* $PREBUILD_TARGET
    # Remove the previously unziped archive
    [ -d $PREBUILD_TARGET/cloud ] && sudo rm -Rf $PREBUILD_TARGET/cloud
}
for role in mysql slave install-server-vm softwarefactory; do
    role=${role}-${SF_VER}
    curl -s -o ${TEMP_DIR}/${role}.md5 ${BASE_URL}/${role}.md5 || continue
    # Swift does not return 404 but 'Not Found'
    grep -q 'Not Found' ${TEMP_DIR}/${role}.md5 && continue
    diff ${TEMP_DIR}/${role}.md5 ${UPSTREAM}/${role}.md5 || {
        sudo curl -s -o ${UPSTREAM}/${role}.edeploy ${BASE_URL}/${role}.edeploy
        sudo curl -s -o ${UPSTREAM}/${role}.edeploy.md5 ${BASE_URL}/${role}.edeploy.md5
        sudo mv -f ${TEMP_DIR}/${role}.md5 ${UPSTREAM}/${role}.md5
        role_md5=$(cat ${UPSTREAM}/${role}.edeploy | md5sum - | cut -d ' ' -f1)
        [ "${role_md5}" != "$(cat ${UPSTREAM}/${role}.edeploy.md5 | cut -d ' ' -f1)" ] && {
            echo "${role} archive md5 mismatch ! exit."
            exit 1
        }
    }
done
rm -Rf ${TEMP_DIR}

# Uncompress prebuild images if needed
cd $PREBUILD_TARGET
[ ! -d cloud ] && {
    sudo mkdir cloud
    sudo tar -xzf $cloud_img -C cloud
    sudo touch cloud.done
}
[ ! -d install-server ] && {
    sudo mkdir install-server
    sudo tar -xzf $install_server_img -C install-server
    sudo touch install-server.done
}
cd -

cd $SF_ROLES
[ ! -d "$BUILD_DIR/install/${DVER}-${SF_REL}" ] && sudo mkdir -p $BUILD_DIR/install/${DVER}-${SF_REL}

build_role "mysql" $(cat mysql.install functions | md5sum | awk '{ print $1}')
ME=$?
build_role "slave" $(cat slave.install functions | md5sum | awk '{ print $1}')
SE=$?
build_role "softwarefactory"   $(cd ..; find ${SF_DEPS} -type f | sort | grep -v '\.tox' | xargs cat | md5sum | awk '{ print $1}')
SFE=$?
build_role "install-server-vm" $(cd ..; find ${IS_DEPS} -type f | sort | grep -v '\.tox' | xargs cat | md5sum | awk '{ print $1}')
IE=$?

exit $[ $ME + $SE + $SFE + $IE ];
