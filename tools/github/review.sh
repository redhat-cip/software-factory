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

if [[ -z "$3" ]]; then
    echo "Usage: $0 <owner> <repository> <pull-request number>"
    echo "Example: $0 enovance edeploy-software-factory-roles 4"
    exit 1
fi

OWNER=$1
REPO=$2
PR=$3
TEMPDIR=`mktemp -d -t "github-$OWNER-$REPO-pullrequest-$PR-XXXXXX"`
cd $TEMPDIR
git clone git@github.com:$OWNER/$REPO.git
cd $TEMPDIR/$REPO/.git
sed -i 's#\[remote "origin"\]#\[remote "origin"\]\n\tfetch = +refs/pull/*/head:refs/pull/origin/*#' config
cd $TEMPDIR/$REPO
git fetch origin
git checkout -b pullrequest_$PR pull/origin/$PR
git rebase master
git review -s


commitmsg="Merge pull request $PR


"
commitmsg+=`git log --format=%B pullrequest_$PR --not master`
git reset --soft master  # squash commits into one
git commit -a -m "$commitmsg"
git review
