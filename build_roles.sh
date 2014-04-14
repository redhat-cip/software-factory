#!/bin/sh

set -e
set -x

SKIP_CLEAN_ROLES="y"

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

[ ! -d "$BUILD_DIR" ] && mkdir -p $BUILD_DIR

if [ "$SKIP_CLEAN_ROLES" != "y" ]; then
    [ -d "$BUILD_DIR/install" ] && rm -Rf $BUILD_DIR/install
fi
[ ! -d "$CLONES_DIR" ] && mkdir -p $CLONES_DIR

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
    sed -i '/gem install/ s/^/HOME=\/root /' install-server.install
    sed -i "/rake make/ s/$/ python-pip/" install-server.install
    cd -
}

cd $EDEPLOY/build
sudo make TOP=$BUILD_DIR base

cd $EDEPLOY_ROLES
sudo make TOP=$BUILD_DIR install-server

cd $SF_ROLES
sudo make TOP=$BUILD_DIR ldap
sudo make TOP=$BUILD_DIR mysql
sudo make TOP=$BUILD_DIR softwarefactory
