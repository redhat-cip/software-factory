#!/bin/bash

OLDPWD=`pwd`

if [ "$1" == "--functional" ]; then
    shift
    # export SF_SKIP_BOOTSTRAP=1 to... skip bootstrap step
    nosetests -s -v tests/ $*
    exit $?
fi

echo -e "\nTesting puppet manifests for Gerrit"
cd puppet/modules/gerrit && ./runtests.sh
cd $OLDPWD
echo -e "\n"

echo -e "\nTesting puppet manifests for Jenkins"
cd puppet/modules/jenkins && ./runtests.sh
cd $OLDPWD
echo -e "\n"

echo -e "\nTesting puppet manifests for Redmine"
cd puppet/modules/redmine  && ./runtests.sh
cd $OLDPWD
echo -e "\n"


echo -e "\nFLAKE8 tests"
find . -iname "*.py" | xargs flake8
echo -e "\n"
