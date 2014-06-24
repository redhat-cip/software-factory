#!/bin/bash

set -e
set -x

SF_REL=${SF_REL:-0.9.0}
EDEPLOY_TAG=master
EDEPLOY_ROLES_TAG=master

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
WORKSPACE=/var/lib/sf
CLONES_DIR=$WORKSPACE/git
BUILD_DIR=$WORKSPACE/roles

EDEPLOY=$WORKSPACE/git/edeploy-${EDEPLOY_TAG}/
EDEPLOY_ROLES=$WORKSPACE/git/edeploy-roles-${EDEPLOY_ROLES_TAG}/
SF_ROLES=$CURRENT/edeploy/

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

if [ ! -d "${EDEPLOY}" ]; then
    git clone $EDEPLOY_PROJECT ${EDEPLOY}
fi

cd $EDEPLOY/build
git checkout $EDEPLOY_TAG
git pull
EDEPLOY_REL=$(make version)
cd -

if [ ! -d "${EDEPLOY_ROLES}" ]; then
    git clone $EDEPLOY_ROLES_PROJECT ${EDEPLOY_ROLES}
fi

cd ${EDEPLOY_ROLES}
git checkout $EDEPLOY_ROLES_TAG
git pull
EDEPLOY_ROLES_REL=$(make version)
cd -

# Prepare prebuild roles
PREBUILD_TARGET=$WORKSPACE/roles/install/$EDEPLOY_ROLES_REL
[ ! -d $PREBUILD_TARGET ] && {
    sudo mkdir -p $PREBUILD_TARGET
    sudo chown ${USER}:root $PREBUILD_TARGET
}
cloud_img="cloud-$EDEPLOY_ROLES_REL.edeploy"
install_server_img="install-server-$EDEPLOY_ROLES_REL.edeploy"
scp -o StrictHostKeyChecking=no $EDEPLOY_ROLES_SRC_ARCHIVES/$install_server_img.md5 /tmp
scp -o StrictHostKeyChecking=no $EDEPLOY_ROLES_SRC_ARCHIVES/$cloud_img.md5 /tmp
[ ! -f $PREBUILD_TARGET/$install_server_img.md5 ] && touch $PREBUILD_TARGET/$install_server_img.md5 
diff $PREBUILD_TARGET/$install_server_img.md5 /tmp/$install_server_img.md5 || {
    scp -o StrictHostKeyChecking=no $EDEPLOY_ROLES_SRC_ARCHIVES/$install_server_img* $PREBUILD_TARGET/
    # Remove the previously unziped archive
    [ -d $PREBUILD_TARGET/install-server ] && sudo rm -Rf $PREBUILD_TARGET/install-server 
}
[ ! -f $PREBUILD_TARGET/$cloud_img.md5 ] && touch $PREBUILD_TARGET/$cloud_img.md5 
diff $PREBUILD_TARGET/$cloud_img.md5 /tmp/$cloud_img.md5 || {
    scp -o StrictHostKeyChecking=no $EDEPLOY_ROLES_SRC_ARCHIVES/$cloud_img* $PREBUILD_TARGET/
    # Remove the previously unziped archive
    [ -d $PREBUILD_TARGET/cloud ] && sudo rm -Rf $PREBUILD_TARGET/cloud
}

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
sudo mkdir -p $BUILD_DIR/install/D7-H.${SF_REL}
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_PATH=${EDEPLOY} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} ldap
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_PATH=${EDEPLOY} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} mysql
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_PATH=${EDEPLOY} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} slave
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL}  EDEPLOY_PATH=${EDEPLOY} EDEPLOY_ROLES_PATH=${EDEPLOY_ROLES} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} softwarefactory
sudo make TOP=$BUILD_DIR $VIRTUALIZED SF_REL=${SF_REL} EDEPLOY_PATH=${EDEPLOY} PREBUILD_EDR_TARGET=${EDEPLOY_ROLES_REL} install-server-vm
RET=$?

exit $RET
