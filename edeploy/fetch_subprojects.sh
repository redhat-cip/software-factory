#!/bin/bash

set -e

echo "PREPARE SUBPROJECTS DIRECTORIES"

# If this script is run in our job runner the
# ZUUL_PROJECT will be set
[ -n "$ZUUL_PROJECT" ] && IN_ZUUL=1 || IN_ZUUL=0
[ $IN_ZUUL -eq 1 ] && echo "Triggered by Zuul ..."

function pin_subprojects_for_tag {
    tagname=$(git name-rev --tags --name-only $(git rev-parse HEAD))
    if [ "$tagname" != "undefined" ]; then
        echo "This is a tagged release; using pinned versions of subprojects to build images."
        PYSFLIB_REV=${PYSFLIB_PINNED_VERSION}
        CAUTH_REV=${CAUTH_PINNED_VERSION}
        MANAGESF_REV=${MANAGESF_PINNED_VERSION}
    else
        echo "This is a non-tagged release; using current versions of subprojects to build images."
    fi
}

# if the build isn't triggered by Zuul, pin the versions if this is a tag build
[ $IN_ZUUL -eq 0 ] && pin_subprojects_for_tag

PYSFLIB_REV=${PYSFLIB_REV:="master"}
CAUTH_REV=${CAUTH_REV:="master"}
MANAGESF_REV=${MANAGESF_REV:="master"}

# Default paths to find cloned dependencies
PYSFLIB_CLONED_PATH=${PYSFLIB_CLONED_PATH:="${PWD}/../deps/pysflib"}
CAUTH_CLONED_PATH=${CAUTH_CLONED_PATH:="${PWD}/../deps/cauth"}
MANAGESF_CLONED_PATH=${MANAGESF_CLONED_PATH:="${PWD}/../deps/managesf"}

# Default repo for deps if we need to fetch them
PYSFLIB_REPO=${PYSFLIB_REPO:="http://softwarefactory.enovance.com/r/pysflib"}
CAUTH_REPO=${CAUTH_REPO:="http://softwarefactory.enovance.com/r/cauth"}
MANAGESF_REPO=${MANAGESF_REPO:="http://softwarefactory.enovance.com/r/managesf"}

# Check if dependencies are present locally
# Our automatic job runner must have cloned the deps
[ -d $PYSFLIB_CLONED_PATH -a $IN_ZUUL -eq 1 ] && PYSFLIB_FETCH_MODE="local" || PYSFLIB_FETCH_MODE="remote"
[ -d $CAUTH_CLONED_PATH -a $IN_ZUUL -eq 1 ] && CAUTH_FETCH_MODE="local" || CAUTH_FETCH_MODE="remote"
[ -d $MANAGESF_CLONED_PATH -a $IN_ZUUL -eq 1 ] && MANAGESF_FETCH_MODE="local" || MANAGESF_FETCH_MODE="remote"

for PROJECT in "PYSFLIB" "CAUTH" "MANAGESF"; do
    eval PROJECT_FETCH_MODE=\$${PROJECT}_FETCH_MODE
    eval PROJECT_CLONED_PATH=\$${PROJECT}_CLONED_PATH
    eval PROJECT_REPO=\$${PROJECT}_REPO
    eval PROJECT_REV=\$${PROJECT}_REV
    eval PROJECT_KEEP=\$${PROJECT}_KEEP
    if [ "$PROJECT_FETCH_MODE" = "remote" ]; then
        if [ -z "$PROJECT_KEEP" ]; then
            echo "Fetch $PROJECT:$PROJECT_REV in $PROJECT_CLONED_PATH."
            [ -d $PROJECT_CLONED_PATH ] && rm -Rf $PROJECT_CLONED_PATH
            (git clone $PROJECT_REPO $PROJECT_CLONED_PATH &> /dev/null && cd $PROJECT_CLONED_PATH) || { echo "Fail to fetch $PROJECT" && exit 1; }
            (cd $PROJECT_CLONED_PATH && git checkout $PROJECT_REV) &> /dev/null || { echo "Fail to checkout rev:$PROJECT_REV" && exit 1; }
        else
            echo "(Forced) Use local source from $PROJECT_CLONED_PATH"
        fi
    else
        echo "Use local source from $PROJECT_CLONED_PATH"
    fi
    (cd $PROJECT_CLONED_PATH && echo "-> $PROJECT head is: $(git log --pretty=oneline --abbrev-commit HEAD | head -1)")
done
