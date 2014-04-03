#!/bin/bash
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

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
