#!/bin/bash

# Copyright (C) 2015 eNovance/Red Hat <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

function get_latest_version_in_pypi {
    version=$(GET http://pypi.python.org/pypi/$1/json | grep \"version\" | awk '{print $2}' | tr -d '",')
    echo $version
}

if [ ! -z "$ZUUL_PROJECT" ]; then
    REQS=${ZUUL_PROJECT}/requirements.txt
else
    REQS=$1
fi
OLDREQS=${REQS}.bak
NEWREQS=${REQS}.new

TEST_NEWREQS=false

LIBPATH=$(dirname $(readlink -f $REQS))

cp $REQS $OLDREQS
cp $REQS $NEWREQS


for req in $(cat $OLDREQS); do
    if [[ $req =~ "==" ]]; then
        lib=$(echo $req|awk -F "==" '{print $1}')
        ver=$(echo $req|awk -F '==' '{print $2}')
        latest=$(get_latest_version_in_pypi $lib)
        if [[ ! $ver == $latest ]]; then
            echo "$lib can be upgraded from $ver to $latest."
            sed -i "s/^${lib}==.*$/${lib}==${latest}/" $REQS
            echo "Running tests with latest version ..."
            cd $LIBPATH > /dev/null 2>&1
            tox_results=$(tox --recreate)
            o=$?
            cd - > /dev/null 2>&1
            if [[ $o == "0" ]]; then
                sed -i "s/^${lib}==.*$/${lib}==${latest}/" $NEWREQS
                echo "SUCCESS !"
                echo "---------"
                TEST_NEWREQS=true
            else
                echo "FAILED !"
                echo "--------"
            fi
            cp $OLDREQS $REQS
        fi
    fi
done

if [ "$TEST_NEWREQS" = true ]; then
    echo "Testing the fully upgraded requirements ..."
    cp $NEWREQS $REQS
    cd $LIBPATH > /dev/null 2>&1
    tox_results=$(tox --recreate)
    if [[ $? == "0" ]]; then
        cd - > /dev/null 2>&1
        echo "SUCCESS !"
        echo "---------"
        echo "You can use the following requirements.txt:"
        echo ""
        cat $NEWREQS
    else
        cd - > /dev/null 2>&1
        echo "FAILED !"
        echo "--------"
    fi
else
    echo "Nothing to do."
fi
cp $OLDREQS $REQS
rm $OLDREQS $NEWREQS
