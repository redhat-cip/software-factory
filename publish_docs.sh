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

# Environment variables HOST, ACCOUNT, CONTAINER and SECRET must be set!

# python-swiftclient and python-keystoneclient must be installed
# Create a container with : swift post sfdocs
# Add unauthenticated read permission : swift post sfdocs -r '.r:*'
# Create a tempurl Key used to upload doc files : swift post -m Temp-URL-Key:1234

# This script must be call like that :
# SECRET='1234' ACCOUNT='***REMOVED***' CONTAINER='sfdocs' HOST='***REMOVED***' ./publish_docs.sh

set -e

BUILDDIR=/tmp/_build
[ -d $BUILDDIR ] && rm -Rf $BUILDDIR

echo "Build docs ..."
cd docs

make BUILDDIR=$BUILDDIR html &> /dev/null
cd $BUILDDIR

echo "Export docs ..."
for OBJECT in `find $1 -type f`; do
    OBJECT=`echo $OBJECT | sed 's|^\./||'`
    SWIFT_PATH="/v1/${ACCOUNT}/${CONTAINER}/${OBJECT}"
    TEMPURL=`swift tempurl PUT 3600 ${SWIFT_PATH} ${SECRET}`
    curl -f -i -X PUT --upload-file "$OBJECT" "http://${HOST}${TEMPURL}" &> /dev/null && echo -n '.' || { echo 'Fail !'; exit 1; }
done
cd - &> /dev/null
echo
echo "Done"
rm -rf $BUILDDIR

echo "Docs are accessible here :"
echo "http://${HOST}/v1/${ACCOUNT}/${CONTAINER}/index.html"
