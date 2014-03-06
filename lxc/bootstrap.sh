#!/bin/bash

. ../function.sh

ROLES="puppetmaster ldap mysql jenkins gerrit jenkins-slave01 jenkins-slave02 edeploy-server"
EDEPLOY_LXC=/srv/edeploy-lxc/edeploy-lxc

if [ -z "$1" ] || [ "$1" == "start" ]; then
    new_build
    cp sf-lxc.yaml ${BUILD}/sf-host.yaml
    mkdir -p /var/lib/debootstrap/install/D7-H.1.0.0/puppetmaster/etc/puppet/{modules,manifests}
    rsync -a ../puppet/modules/ /var/lib/debootstrap/install/D7-H.1.0.0/puppetmaster/etc/puppet/modules/
    rsync -a ../puppet/manifests/ /var/lib/debootstrap/install/D7-H.1.0.0/puppetmaster/etc/puppet/manifests/
    # We alreay have puppetmaster IP, so we can generate cloudinit
    generate_cloudinit
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml restart || exit -1
    sf_postconfigure
elif [ "$1" == "stop" ]; then
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml stop
elif [ "$1" == "clean" ]; then
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml stop
    rm -Rf ${BUILD}
else
    echo "usage: $0 [start|stop|clean]"
fi
