#!/bin/bash

# publish docs

set -e
[ -n "$DEBUG" ] && set -x

. ./role_configrc

CONTAINER="sfdocs"

BUILDDIR=$(mktemp -d /tmp/sfdocs_buildXXXXXXX)
trap "rm -Rf ${BUILDDIR}" EXIT

echo "Build docs ..."
(cd ${DOCDIR}; make MANAGESF_CLONED_PATH=${MANAGESF_CLONED_PATH} CAUTH_CLONED_PATH=${CAUTH_CLONED_PATH} BUILDDIR=${BUILDDIR} html &> /dev/null)

(
    cd $DOCBUILD/html

    echo "Export docs ..."
    for OBJECT in `find $1 -type f`; do
        OBJECT=`echo $OBJECT | sed 's|^\./||'`
        SWIFT_PATH="/v1/AUTH_${SWIFT_ACCOUNT}/${CONTAINER}/${OBJECT}"
        TEMPURL=`swift tempurl PUT 120 ${SWIFT_PATH} ${TEMP_URL_KEY}`
        curl -f -i -X PUT --upload-file "$OBJECT" "${SWIFT_BASE_URL}${TEMPURL}" && echo -n '.' || { echo 'Fail !'; exit 1; }
    done
)
echo
echo "Docs are accessible here :"
echo "${SWIFT_BASE_URL}/v1/${SWIFT_ACCOUNT}/${CONTAINER}/index.html"
echo "$0: SUCCESS"
exit 0
