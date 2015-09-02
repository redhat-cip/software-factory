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

echo "Fetching logs ... "

dlogs=/tmp/logs

[ -d $dlogs ] && rm -Rf $dlogs
mkdir $dlogs

# Boostrap process log
cp /var/log/sf-bootstrap.log $dlogs/

echo "Checking for edeploy logs ..."
[ -f /var/lib/edeploy/rsync_*.out ] && edeploy_logs=true || edeploy_logs=false

# Retrieve Syslog
for role in gerrit redmine jenkins mysql managesf puppetmaster slave; do
    mkdir -p $dlogs/${role}
    ip=$(getip_from_yaml ${role})
    scp root@${ip}:/var/log/syslog $dlogs/${role} &> /dev/null
    scp root@${ip}:/var/log/messages $dlogs/${role} &> /dev/null
    if [ $edeploy_logs = true ]; then
        mkdir $dlogs/${role}/edeploy
        scp root@${ip}:/var/lib/edeploy/rsync_*.out $dlogs/${role}/edeploy &> /dev/null
    fi
    ssh root@${ip} "journalctl -la --no-pager > /tmp/syslog"
    [ "$?" == "0" ]  && scp root@${ip}:/tmp/syslog $dlogs/${role} &> /dev/null
    # Check for failed units and retrieve their journal (except for units known to not work)
    ssh root@${ip} "systemctl | grep failed | grep -v '\(audit\|avahi-daemon\|cloud-config\|kdump\)'" > ${dlogs}/${role}/systemd_failed
    for unit in $(cat ${dlogs}/${role}/systemd_failed | awk '{ print $1 }'); do
        echo -e "\n== ${unit} ==" >> ${dlogs}/${role}/systemd_failed
        ssh root@${ip} "journalctl -u $unit" >> ${dlogs}/${role}/systemd_failed
    done
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

scp -r root@`getip_from_yaml redmine`:/usr/share/redmine/log/ $dlogs/redmine/ &> /dev/null
scp root@`getip_from_yaml managesf`:/var/log/managesf/managesf.log $dlogs/managesf/ &> /dev/null
scp root@`getip_from_yaml managesf`:/var/log/cauth/cauth.log $dlogs/managesf/ &> /dev/null
scp -r root@`getip_from_yaml managesf`:/var/log/apache2/ $dlogs/managesf/ &> /dev/null
scp -r root@`getip_from_yaml managesf`:/var/log/httpd/ $dlogs/managesf/ &> /dev/null
scp -r root@`getip_from_yaml gerrit`:/var/log/httpd/ $dlogs/gerrit/ &> /dev/null
scp -r root@`getip_from_yaml jenkins`:/var/log/httpd/ $dlogs/jenkins/ &> /dev/null
scp -r root@`getip_from_yaml jenkins`:/var/log/zuul $dlogs/zuul/ &> /dev/null
scp -r root@`getip_from_yaml jenkins`:/var/lib/jenkins/jobs/ $dlogs/jenkins/ &> /dev/null
scp -r root@`getip_from_yaml jenkins`:/var/lib/jenkins/logs/ $dlogs/jenkins/ &> /dev/null
scp -r root@`getip_from_yaml jenkins`:/root/config/ $dlogs/config-project &> /dev/null
scp root@`getip_from_yaml puppetmaster`:/tmp/debug $dlogs/puppetmaster/ &> /dev/null

echo "Done."

set -x
set -e
