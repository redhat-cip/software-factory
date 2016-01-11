#!/bin/bash
# SF environment requirements

if [ ! -f "/etc/yum.repos.d/epel.repo" ]; then
    echo "(+) Adds epel-release..."
    sudo yum install -y epel-release
fi
if [ ! -f "/usr/bin/pip" ]; then
    echo "(+) Installing python-pip..."
    sudo yum install -y python-pip
    sudo pip install --upgrade pip
fi
if [ ! -f "/usr/bin/git-review" ] || [ ! -f "/usr/bin/tox" ] || [ ! -f "/usr/bin/ansible" ] || [ ! -f "/usr/bin/nosetests" ]; then
    echo "(+) Installing test-requirements..."
    sudo pip install -r test-requirements.txt
fi
