#!/bin/bash

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
