#!/bin/bash

set -e
set -x

EDEPLOY_REL=${EDEPLOY_REL:-1.2.0}
SF_REL=${SF_REL:-0.9.0}

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


EDEPLOY=$WORKSPACE/git/edeploy-${EDEPLOY_REL}/
EDEPLOY_ROLES=$WORKSPACE/git/edeploy-roles-${EDEPLOY_REL}/
SF_ROLES=$CURRENT/edeploy/

BOOTSTRAPPER=$SF_ROLES/puppet_bootstrapper.sh

function clear_mountpoint {
    # Clean mountpoints
    set +x
    grep '\/var.*proc' /proc/mounts | awk '{ print $2 }' | while read mountpoint; do
        echo "[+] UMOUNT ${mountpoint}"
        sudo umount ${mountpoint};
    done
    grep '\/var.*lxc' /proc/mounts | awk '{ print $2 }' | while read mountpoint; do
        echo "[+] UMOUNT ${mountpoint}"
        sudo umount ${mountpoint};
    done
    set -x
}

clear_mountpoint

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

[ ! -d ${EDEPLOY} ] && {
    (
        git clone $EDEPLOY_PROJECT ${EDEPLOY}
        cd $EDEPLOY/build
        git checkout H.$EDEPLOY_REL
    )
}

[ ! -d "${EDEPLOY_ROLES}" ] && {
    (
        git clone $EDEPLOY_ROLES_PROJECT ${EDEPLOY_ROLES}
        cd ${EDEPLOY_ROLES}
        git checkout H.$EDEPLOY_REL
    )
}

cd $EDEPLOY/build
sudo make TOP=$BUILD_DIR STRIPPED_TARGET=false REL=${EDEPLOY_REL} base
clear_mountpoint

cd $SF_ROLES
# the nesteed puppet-master role need to be fetched from edeploy-roles
sudo mkdir -p $BUILD_DIR/install/D7-H.${SF_REL}
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_ROLES=$EDEPLOY_ROLES vm
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} EDEPLOY_ROLES=$EDEPLOY_ROLES install-server-vm
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} ldap
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} mysql
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} slave
clear_mountpoint
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_REL=${EDEPLOY_REL} softwarefactory
RET=$?
clear_mountpoint

exit $RET
