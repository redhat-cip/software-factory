#!/bin/sh

set -x

# Sanity check
[ -d ${HOME}/.ssh ] || mkdir ${HOME}/.ssh
[ -f ${HOME}/.ssh/id_rsa ] || ssh-keygen -f ${HOME}/.ssh/id_rsa -N ''

which virsh || {
    sudo yum install -y libvirt-daemon-lxc
    sudo systemctl restart libvirtd
}

# Make sure no bare lxc instances are running
if [ "$1" == "stop" ]; then
    for instance in $(sudo lxc-ls); do
        sudo lxc-stop --kill --name ${instance}
    done
fi

exec sudo python start.py $*
