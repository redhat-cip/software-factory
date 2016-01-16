#!/bin/bash
# SF environment requirements

bash ./rpm-requirements.sh

if [ ! -f "/etc/yum.repos.d/epel.repo" ]; then
    echo "(+) Adds epel-release..."
    sudo yum install -y epel-release
fi
function test_which {
    which $1 &> /dev/null && return 0 || return 1
}
test_which pip || {
    echo "(+) Installing python-pip..."
    sudo yum install -y python-pip
    sudo pip install --upgrade pip
}
test_which git-review && test_which tox && test_which ansible && test_which nosetests || {
    echo "(+) Installing test-requirements..."
    sudo pip install -r test-requirements.txt
}
