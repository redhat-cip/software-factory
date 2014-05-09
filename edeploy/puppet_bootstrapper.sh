#!/bin/bash

# Here we prepare an archive that contains the needed stuff
# that need to stored on our puppet-master node.

# Puppet (hiera/manifest/modules) for SF
PUPPET=../puppet
SERVERSPEC=../serverspec
TESTS=../tests
TOOLS=../tools
SCRIPT1=../bootstraps/functions.sh
SCRIPT2=../bootstraps/bootstrap.sh
# Temporary dir before archiving
NAME=puppet-bootstrapper
TARGET=/tmp/$NAME


[ -d $TARGET ] && rm -Rf $TARGET
mkdir $TARGET
cp -Rf $PUPPET $SERVERSPEC $TESTS $TOOLS $TARGET/
cp $SCRIPT1 $SCRIPT2 $TARGET/
cd /tmp
tar -czf ${NAME}.tar.gz $NAME
cd -
