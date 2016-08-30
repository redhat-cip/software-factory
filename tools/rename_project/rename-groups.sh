#!/bin/bash

set -ex

[ -z "$1" ] && {
    echo "Please provide old name as arg 1"
    exit 1
}
[ -z "$2" ] && {
    echo "Please provide new name as arg 2"
    exit 1
}

ssh-keyscan -p 29418 managesf | sed 's/managesf/\[managesf\]:29418/' >> ~/.ssh/known_hosts
ptl=$(ssh -i /root/sf-bootstrap-data/ssh_keys/gerrit_service_rsa -p 29418 admin@managesf gerrit ls-groups | grep "$2-ptl" || true)
if [ -z "$ptl" ]; then
    ssh -i /root/sf-bootstrap-data/ssh_keys/gerrit_service_rsa -p 29418 admin@managesf gerrit rename-group "$1-ptl" "$2-ptl"
fi

core=$(ssh -i /root/sf-bootstrap-data/ssh_keys/gerrit_service_rsa -p 29418 admin@managesf gerrit ls-groups | grep "$2-core" || true)
if [ -z "$core" ]; then
    ssh -i /root/sf-bootstrap-data/ssh_keys/gerrit_service_rsa -p 29418 admin@managesf gerrit rename-group "$1-core" "$2-core"
fi
