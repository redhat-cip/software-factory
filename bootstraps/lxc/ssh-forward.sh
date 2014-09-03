#!/bin/bash
set -x

# Start that script on your laptop to get access
# to SF services that run on LXC containers on the $host
# node. Set accordingly your /etc/hosts to have name resolution
# to enjoy SSO feature. Please run that script as root and
# also add user's ssh key before running the script i.e
#sudo -i
#ssh-agent bash
#ssh-add <path to user's key i.e /home/<user_name>/.ssh/id_rsa

#The LXC host, please modify sf-build with  your lxc host
host=ubuntu@sf-build

pkill -f "ssh -N -L 127.0.10.*"

sleep 2

# Gerrit
ssh -N -L 127.0.10.1:80:192.168.134.52:80 $host &
# Redmine
ssh -N -L 127.0.10.2:80:192.168.134.51:80 $host &
# Jenkins
ssh -N -L 127.0.10.3:8080:192.168.134.53:8080 $host &
# Zuul status
ssh -N -L 127.0.10.3:80:192.168.134.53:80 $host &
# Webinterface
ssh -N -L 127.0.10.4:80:192.168.134.54:80 $host &

echo "\
You can add that to you /etc/hosts
127.0.10.1 gerrit.tests.dom gerrit
127.0.10.2 redmine.tests.dom redmine
127.0.10.3 jenkins.tests.dom jenkins
127.0.10.4 managesf.tests.dom auth.tests.dom managesf auth
"
