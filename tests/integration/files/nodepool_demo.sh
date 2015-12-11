#!/bin/bash

sudo edeploy activate-pkgmngr
sudo userdel jenkins

echo $(echo $SSH_CONNECTION | awk '{ print $1 }' ) sftests.com | sudo tee -a /etc/hosts
cat /etc/hosts

. base.sh
