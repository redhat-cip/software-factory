#!/bin/bash
# simplified version from upstream

GERRIT_URL="$1"
GIT_URL=${GERRIT_URL}/${GERRIT_PROJECT}

set -x
if [[ ! -e .git ]]
then
    ls -a
    rm -fr .[^.]* *
    git clone ${GIT_URL} .
fi
git remote set-url origin ${GIT_URL}

# attempt to work around bugs 925790 and 1229352
if ! git remote update
then
    echo "The remote update failed, so garbage collecting before trying again."
    git gc
    git remote update
fi

git reset --hard
if ! git clean -x -f -d -q ; then
    sleep 1
    git clean -x -f -d -q
fi


git fetch ${GIT_URL} ${GERRIT_REFSPEC}
git checkout FETCH_HEAD
git reset --hard FETCH_HEAD
if ! git clean -x -f -d -q ; then
    sleep 1
    git clean -x -f -d -q
fi
