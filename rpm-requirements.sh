#!/bin/bash
# SF environment requirements

PKGS=""
which wget &> /dev/null         || PKGS="${PKGS} wget"
which gcc &> /dev/null          || PKGS="${PKGS} gcc"
which git &> /dev/null          || PKGS="${PKGS} git"
which curl &> /dev/null         || PKGS="${PKGS} curl"
which patch &> /dev/null        || PKGS="${PKGS} patch"
which sphinx-build &> /dev/null || PKGS="${PKGS} python-sphinx"
which virtualenv &> /dev/null   || PKGS="${PKGS} python-virtualenv"
which pip &> /dev/null          || PKGS="${PKGS} python-pip"
[ -f "/usr/include/ffi.h" ]     || PKGS="${PKGS} libffi-devel mariadb-devel openldap-devel openssl-devel"
[ -f "/usr/include/python2.7/Python.h" ] || PKGS="${PKGS} python-devel"
[ -d "/usr/lib64/python2.7/site-packages/Crypto/" ] || PKGS="${PKGS} python-crypto"

if [ ! -f "/etc/yum.repos.d/epel.repo" ]; then
    echo "(+) Adds epel-release..."
    sudo yum install -y epel-release
fi

if [ ! -z "${PKGS}" ]; then
    echo "(+) Installing build requirement..."
    sudo yum install -y $PKGS
fi
