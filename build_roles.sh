#!/bin/bash

set -e
set -x

EDEPLOY_REL=${EDEPLOY_REL:-D7-1.4.0}
SF_REL=${SF_REL:-0.9.0}
EDEPLOY_TAG=1.4.0
EDEPLOY_ROLES_TAG=I.1.0.0

if [ "$(sudo losetup -a | wc -l)" -gt 5 ]; then
    # TODO: fix/report this
    echo "Not enough loopback device. This is a known bug, please reboot this jenkins node"
    exit -1
fi

SKIP_CLEAN_ROLES=${SKIP_CLEAN_ROLES:-y}
VIRTUALIZED=""
[ -n "$VIRT" ] && {
    VIRTUALIZED="VIRTUALIZED=params.virt"
}

EDEPLOY_PROJECT=https://github.com/enovance/edeploy.git
EDEPLOY_ROLES_PROJECT=https://github.com/enovance/edeploy-roles.git

CURRENT=`pwd`
WORKSPACE=/var/lib/sf
CLONES_DIR=$WORKSPACE/git
BUILD_DIR=$WORKSPACE/roles


EDEPLOY=$WORKSPACE/git/edeploy-${EDEPLOY_TAG}/
EDEPLOY_ROLES=$WORKSPACE/git/edeploy-roles-${EDEPLOY_ROLES_TAG}/
SF_ROLES=$CURRENT/edeploy/

BOOTSTRAPPER=$SF_ROLES/puppet_bootstrapper.sh

function clear_mountpoint {
    # Clean mountpoints
    set +x
    set +e
    grep '\/var.*proc' /proc/mounts | awk '{ print $2 }' | while read mountpoint; do
        echo "[+] UMOUNT ${mountpoint}"
        sudo umount ${mountpoint};
    done
    grep '\/var.*lxc' /proc/mounts | awk '{ print $2 }' | while read mountpoint; do
        echo "[+] UMOUNT ${mountpoint}"
        sudo umount ${mountpoint};
    done
    set -e
    set -x
}

if [ ! -d $WORKSPACE ]; then
    sudo mkdir -m 0770 $WORKSPACE
    sudo chown ${USER}:root $WORKSPACE
fi

[ ! -d "$BUILD_DIR" ] && sudo mkdir -p $BUILD_DIR

if [ "$SKIP_CLEAN_ROLES" != "y" ]; then
    [ -d "$BUILD_DIR/install" ] && sudo rm -Rf $BUILD_DIR/install
fi
[ ! -d "$CLONES_DIR" ] && sudo mkdir -p $CLONES_DIR
sudo chown -R ${USER} ${CLONES_DIR}

# We must handle master better, if we target master we need
# to enter in $EDEPLOY and pull.
[ "$EDEPLOY_TAG" == "master" ] && rm -Rf ${EDEPLOY}

if [ ! -d "${EDEPLOY}" ]; then
    git clone $EDEPLOY_PROJECT ${EDEPLOY}
    cd $EDEPLOY/build
    git checkout $EDEPLOY_TAG
    cd -
fi

# We must handle master better, if we target master we need
# to enter in $EDEPLOY_ROLES and pull.
[ "$EDEPLOY_ROLES_TAG" == "master" ] && rm -Rf ${EDEPLOY_ROLES}

if [ ! -d "${EDEPLOY_ROLES}" ]; then
    git clone $EDEPLOY_ROLES_PROJECT ${EDEPLOY_ROLES}
    cd ${EDEPLOY_ROLES}
    git checkout $EDEPLOY_ROLES_TAG
    cd -
fi

cd $EDEPLOY/build
sudo make TOP=$BUILD_DIR STRIPPED_TARGET=false base
clear_mountpoint

cd $SF_ROLES
sudo mkdir -p $BUILD_DIR/install/D7-H.${SF_REL}
clear_mountpoint
sudo make TOP=$BUILD_DIR SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_PATH=${EDEPLOY} EDEPLOY_ROLES_PATH=${EDEPLOY_ROLES} vm
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_PATH=${EDEPLOY} EDEPLOY_ROLES_PATH=${EDEPLOY_ROLES} install-server-vm
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_PATH=${EDEPLOY} ldap
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_PATH=${EDEPLOY} mysql
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_PATH=${EDEPLOY} slave
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_PATH=${EDEPLOY} softwarefactory
RET=$?
clear_mountpoint

exit $RET
