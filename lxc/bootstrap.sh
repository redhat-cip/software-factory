#!/bin/bash

ROLES="puppetmaster mysql" # ldap redmine jenkins gerrit"
EDEPLOY_LXC=/srv/edeploy-lxc/edeploy-lxc


function getip_from_lxcyaml {
    cat sf-lxc.yaml  | grep -A 2 -B 2 "name: sf-$1$" | grep 'address' | cut -d: -f2 | sed 's/ *//g'
}

function generate_cloudinit {
    PUPPETMASTER_IP=$(getip_from_lxcyaml puppetmaster)
    rm -Rf lxc-cloudinit
    mkdir lxc-cloudinit
    for i in ../cloudinit/*.cloudinit; do
        cat $i | sed "s#.*puppetmaster.pub.*# - echo $PUPPETMASTER_IP puppetmaster.pub >> /etc/hosts#g" > lxc-cloudinit/$(basename $i)
    done
}

function generate_hiera_hosts {
    rm -Rf lxc-hiera
    mkdir lxc-hiera
    echo -e "hosts:\n  localhost:\n    ip: 127.0.0.1" > lxc-hiera/hosts.yaml
    for role in $ROLES; do
        echo "  ${role}.pub:" >> lxc-hiera/hosts.yaml
        echo "    ip: $(getip_from_lxcyaml ${role})" >> lxc-hiera/hosts.yaml
    done
}

if [ -z "$1" ] || [ "$1" == "start" ]; then
    echo "[+] Starting"
    generate_cloudinit
    generate_hiera_hosts
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml restart
    sudo cp lxc-hiera/hosts.yaml /var/lib/lxc/puppetmaster/rootfs/etc/puppet/hiera/hosts.yaml
elif [ "$1" == "stop" ]; then
    echo "[+] Stoping"
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml stop
else
    echo "usage: $0 [start|stop]"
fi
