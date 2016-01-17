#!/bin/bash
# SF environment requirements

bash ./rpm-requirements.sh

PKGS=""
which ansible &> /dev/null    || PKGS="${PKGS} ansible"
which git-review &> /dev/null || PKGS="${PKGS} git-review"
which flake8 &> /dev/null     || PKGS="${PKGS} python-flake8"
if [ ! -z "${PKGS}" ]; then
    echo "(+) Installing test requirement..."
    sudo yum install -y $PKGS
fi
# Check if test-requirements are already installed
which tox &> /dev/null &&       \
which nosetests &> /dev/null && \
which bash8 &> /dev/null &&     \
test -d /usr/lib/python2.7/site-packages/nosetimer || {
    echo "(+) Installing test-requirements..."
    sudo pip install -r test-requirements.txt
}
