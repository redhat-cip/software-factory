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

mh="localhost:9090" # HTTP access for managesf host
gh="sf-gerrit:29418" # SSH access for gerrit host
jh="sf-jenkins" # SSH access for jenkins host
admin="user1" # admin user for accessing gerrit
admin_http_password="userpass"
admin_email="user1@example.com" # Registered email address for admin user
gerrit_ssh_key="/srv/SoftwareFactory/build/data/gerrit_admin_rsa" # gerrit priv key path for admin user
jenkins_ssh_key="/home/ubuntu/.ssh/id_rsa" # ssh key to access jenkins
jenkins_kick_script="/usr/local/jenkins/slave_scripts/kick.sh" # JJB kick start script

dir=`pwd`/$( dirname "${BASH_SOURCE[0]}")
auth=$admin:$admin_http_password

echo ""
echo "==== Creating config project ===="
echo "{\"description\":\"Config repository\"}" | curl "http://$mh/project/config" -X PUT -d @- -H "Content-type: application/json" -H "Authorization: Basic `echo -n $auth | base64`"

echo ""
echo "==== Cloning the config repo ===="
echo "ssh -o StrictHostKeyChecking=no -i $gerrit_ssh_key \$@" > /tmp/ssh_wrapper.sh
chmod +x /tmp/ssh_wrapper.sh
export GIT_SSH="/tmp/ssh_wrapper.sh"
export GIT_COMMITTER_NAME=$admin
export GIT_COMMITTER_EMAIL=$admin_email
git clone ssh://$admin@$gh/config /tmp/config

echo ""
echo "==== Adding JJB files to the config repo ===="
cd /tmp/config
files=`ls $dir/jjb/`
for f in $files
do
    name=`echo "$f" | cut -d'.' -f1`
    cp $dir/jjb/$f /tmp/config/$name
done
git add .

echo ""
echo "==== Commiting the changes ===="
git commit -a --author "$admin <$admin_email>" -m "JJB files"

echo ""
echo "==== Pushing changes ===="
git push origin master

cd $dir
rm -rf /tmp/config
rm -f /tmp/ssh_wrapper.sh

echo ""
echo "==== Kick starting JJB ===="
ssh -i $jenkins_ssh_key -o StrictHostKeyChecking=no root@$jh $jenkins_kick_script

echo ""
echo "Done!"
