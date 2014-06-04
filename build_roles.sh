#!/bin/sh

set -e
set -x

if [ "$(sudo losetup -a | wc -l)" -gt 5 ]; then
    # TODO: fix/report this
    echo "Not enough loopback device. This is a known bug, please reboot this jenkins node"
    exit -1
fi


SKIP_CLEAN_ROLES="y"
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

EDEPLOY=$WORKSPACE/git/edeploy
EDEPLOY_ROLES=$WORKSPACE/git/edeploy-roles/
EDEPLOY_TAG=H.1.0.0
SF_ROLES=$CURRENT/edeploy

BOOTSTRAPPER=$SF_ROLES/puppet_bootstrapper.sh

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

cd $CLONES_DIR
[ ! -d "edeploy" ] && {
    git clone $EDEPLOY_PROJECT
    cd $EDEPLOY/build
    git checkout $EDEPLOY_TAG
    cd -
}
[ ! -d "edeploy-roles" ] && {
    git clone $EDEPLOY_ROLES_PROJECT
    cd $EDEPLOY_ROLES
    git checkout $EDEPLOY_TAG
    cd -
}

cd $EDEPLOY/build
sudo make TOP=$BUILD_DIR base

cd $SF_ROLES
# the nesteed puppet-master role need to be fetched from edeploy-roles
sudo make TOP=$BUILD_DIR $VIRTUALIZED EDEPLOY_ROLES=$EDEPLOY_ROLES install-server-vm
sudo make TOP=$BUILD_DIR $VIRTUALIZED ldap
sudo make TOP=$BUILD_DIR $VIRTUALIZED mysql
sudo make TOP=$BUILD_DIR $VIRTUALIZED slave
sudo make TOP=$BUILD_DIR $VIRTUALIZED softwarefactory
