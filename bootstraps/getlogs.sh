#!/bin/bash
#
# copyright (c) 2014 enovance sas <licensing@enovance.com>
#
# licensed under the apache license, version 2.0 (the "license"); you may
# not use this file except in compliance with the license. you may obtain
# a copy of the license at
#
# http://www.apache.org/licenses/license-2.0
#
# unless required by applicable law or agreed to in writing, software
# distributed under the license is distributed on an "as is" basis, without
# warranties or conditions of any kind, either express or implied. see the
# license for the specific language governing permissions and limitations
# under the license.

# Script that will fetch interesting logs files from
# all SF nodes


source functions.sh

set +x
set +e

echo -n "Fetching logs ... "

dlogs=/tmp/logs

[ -d $dlogs ] && rm -Rf $dlogs
mkdir $dlogs

# Boostrap process log
cp /var/log/sf-bootstrap.log $dlogs/

# Retrieve Syslog
for role in gerrit redmine jenkins mysql managesf commonservices; do
    mkdir $dlogs/${role}
    scp root@`getip_from_yaml ${role}`:/var/log/syslog $dlogs/${role} &> /dev/null
done

# The init option of gerrit.war will rewrite the gerrit config files
# if the provided files does not follow exactly the expected format by gerrit.  
# If there is a rewrite puppet will detect the change in the *.config files
# and then trigger a restart. We want to avoid that because the gerrit restart
# can occured during functional tests. So here we display the changes that can
# appears in the config files (to help debugging).
# We have copied *.config files in /tmp just before the gerrit.war init (see the
# manifest) and create a diff after. Here we just display it to help debug.

scp -r root@`getip_from_yaml gerrit`:/home/gerrit/site_path/logs/ $dlogs/gerrit/ &> /dev/null
scp root@`getip_from_yaml gerrit`:/tmp/config.diff $dlogs/gerrit/ &> /dev/null

scp root@`getip_from_yaml redmine`:/var/log/redmine/default/production.log $dlogs/redmine/ &> /dev/null
scp root@`getip_from_yaml managesf`:/var/log/managesf/managesf.log $dlogs/managesf/ &> /dev/null
scp -r root@`getip_from_yaml managesf`:/var/log/apache2/ $dlogs/managesf/ &> /dev/null
scp -r root@`getip_from_yaml jenkins`:/var/log/zuul $dlogs/zuul/ &> /dev/null
scp root@`getip_from_yaml puppetmaster`:/tmp/debug $dlogs/puppetmaster/ &> /dev/null

echo "Done."

set -x
set -e
