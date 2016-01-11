#!/bin/bash
# SF environment requirements

PKGS=""
function check_packages {
    for pkg in $*; do
        which $pkg &> /dev/null || PKGS="${PKGS} ${pkg}"
    done
}
check_packages patch curl wget git gcc
which sphinx-build &> /dev/null || PKGS="${PKGS} python-sphinx"
which virtualenv &> /dev/null   || PKGS="${PKGS} python-virtualenv"
which pip &> /dev/null          || PKGS="${PKGS} python-pip"
[ -f "/usr/include/python2.7/Python.h" ] || PKGS="${PKGS} python-devel"
[ -f "/usr/include/ffi.h" ]     || PKGS="${PKGS} libffi-devel mariadb-devel openldap-devel openssl-devel"

if [ ! -z "${PKGS}" ]; then
    echo "(+) Installing build requirement..."
    sudo yum install -y $PKGS
fi
