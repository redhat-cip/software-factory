#!/bin/bash

BUILD="../build"
ROLES="puppetmaster mysql ldap redmine jenkins gerrit"
EDEPLOY_LXC=/srv/edeploy-lxc/edeploy-lxc


function getip_from_lxcyaml {
    cat sf-lxc.yaml  | grep -A 2 -B 2 "name: sf-$1$" | grep 'address' | cut -d: -f2 | sed 's/ *//g'
}

function generate_cloudinit {
    OUTPUT=${BUILD}/cloudinit
    PUPPETMASTER_IP=$(getip_from_lxcyaml puppetmaster)
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    for i in ../cloudinit/*.cloudinit; do
        cat $i | sed "s#.*puppetmaster.pub.*# - echo ${PUPPETMASTER_IP} puppetmaster.pub >> /etc/hosts#g" > ${OUTPUT}/$(basename $i)
    done
}

function generate_hiera {
    OUTPUT=${BUILD}/hiera
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}

    # Hosts
    echo -e "hosts:\n  localhost:\n    ip: 127.0.0.1" > ${OUTPUT}/hosts.yaml
    for role in $ROLES; do
        echo "  ${role}.pub:" >> ${OUTPUT}/hosts.yaml
        echo "    ip: $(getip_from_lxcyaml ${role})" >> ${OUTPUT}/hosts.yaml
    done

    # Jenkins ssh key
    JENKINS_PUB="$(cat ${OUTPUT}/../data/jenkins_rsa.pub | cut -d' ' -f2)"
    cat ../puppet/hiera/ssh.yaml | sed "s#JENKINS_PUB_KEY#${JENKINS_PUB}#" > ${OUTPUT}/ssh.yaml
}

function generate_jenkins_key {
    OUTPUT=${BUILD}/data
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa
}

if [ -z "$1" ] || [ "$1" == "start" ]; then
    echo "[+] Starting"
    generate_cloudinit
    generate_jenkins_key
    generate_hiera
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml restart
    sudo scp ${BUILD}/hiera/*.yaml /var/lib/lxc/puppetmaster/rootfs/etc/puppet/hiera/
elif [ "$1" == "stop" ]; then
    echo "[+] Stoping"
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml stop
else
    echo "usage: $0 [start|stop]"
fi
