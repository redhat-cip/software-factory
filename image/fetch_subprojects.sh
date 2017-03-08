#!/bin/bash

set -e

. ./role_configrc
echo "PREPARE SUBPROJECTS DIRECTORIES"

[ -n "$ZUUL_PROJECT" ] && IN_ZUUL=1 || IN_ZUUL=0
[ $IN_ZUUL -eq 1 ] && echo "Triggered by Zuul ..."

PYSFLIB_REV=${PYSFLIB_REV:-"origin/master"}
CAUTH_REV=${CAUTH_REV:-"origin/master"}
MANAGESF_REV=${MANAGESF_REV:-"origin/master"}
SFMANAGER_REV=${SFMANAGER_REV:-"origin/master"}

# Default repo for deps if we need to fetch them
PYSFLIB_REPO=${PYSFLIB_REPO:-"http://softwarefactory-project.io/r/pysflib"}
CAUTH_REPO=${CAUTH_REPO:-"http://softwarefactory-project.io/r/cauth"}
MANAGESF_REPO=${MANAGESF_REPO:-"http://softwarefactory-project.io/r/managesf"}
SFMANAGER_REPO=${SFMANAGER_REPO:-"http://softwarefactory-project.io/r/python-sfmanager"}

# Check if dependencies are present locally
# Our automatic job runner must have cloned the deps
[ -d $PYSFLIB_CLONED_PATH -a $IN_ZUUL -eq 1 ] && PYSFLIB_FETCH_MODE="local" || PYSFLIB_FETCH_MODE="remote"
[ -d $CAUTH_CLONED_PATH -a $IN_ZUUL -eq 1 ] && CAUTH_FETCH_MODE="local" || CAUTH_FETCH_MODE="remote"
[ -d $MANAGESF_CLONED_PATH -a $IN_ZUUL -eq 1 ] && MANAGESF_FETCH_MODE="local" || MANAGESF_FETCH_MODE="remote"
[ -d $SFMANAGER_CLONED_PATH -a $IN_ZUUL -eq 1 ] && SFMANAGER_FETCH_MODE="local" || SFMANAGER_FETCH_MODE="remote"

for PROJECT in "PYSFLIB" "CAUTH" "MANAGESF" "SFMANAGER"; do
    eval PROJECT_FETCH_MODE=\$${PROJECT}_FETCH_MODE
    eval PROJECT_CLONED_PATH=\$${PROJECT}_CLONED_PATH
    eval PROJECT_REPO=\$${PROJECT}_REPO
    eval PROJECT_REV=\$${PROJECT}_REV
    eval PROJECT_KEEP=\$${PROJECT}_KEEP
    if [ "$PROJECT_FETCH_MODE" = "remote" ]; then
        if [ -z "$PROJECT_KEEP" ]; then
            echo "Fetch $PROJECT:$PROJECT_REV in $PROJECT_CLONED_PATH"
            if [ -d $PROJECT_CLONED_PATH ]; then
                (cd $PROJECT_CLONED_PATH; git fetch --all) &> /dev/null
            else
                git clone $PROJECT_REPO $PROJECT_CLONED_PATH &> /dev/null || { echo "Fail to fetch $PROJECT" && exit 1; }
            fi
            (cd $PROJECT_CLONED_PATH && git checkout $PROJECT_REV && git clean -fd) &> /dev/null || { echo "Fail to checkout rev:$PROJECT_REV" && exit 1; }
        else
            echo "(Forced) Use local source from $PROJECT_CLONED_PATH"
        fi
    else
        echo "Use local source from $PROJECT_CLONED_PATH"
        [ "$TAGGED_RELEASE" -eq 1 ] && {
            echo "Tagged release so use the pinned version"
            (cd $PROJECT_CLONED_PATH && git checkout $PROJECT_REV) &> /dev/null || { echo "Fail to checkout rev:$PROJECT_REV" && exit 1; }
        }
    fi
    (cd $PROJECT_CLONED_PATH && echo "-> $PROJECT_CLONED_PATH head is: $(git log --pretty=oneline --abbrev-commit HEAD | head -1)")
done
