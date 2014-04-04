#!/bin/bash

set -x
set -e

SF_PREFIX=${SF_PREFIX:-sf}
export SF_PREFIX

. ../function.sh

ROLES="${SF_PREFIX}-puppetmaster ${SF_PREFIX}-ldap ${SF_PREFIX}-mysql ${SF_PREFIX}-redmine ${SF_PREFIX}-jenkins ${SF_PREFIX}-gerrit"
EDEPLOY_LXC=/srv/edeploy-lxc/edeploy-lxc

if [ -z "$1" ] || [ "$1" == "start" ]; then
    new_build
    # Fix SF_PREFIX bootstrap && manage-sf configuration
    cat sf-lxc.yaml | sed "s/SF_PREFIX/${SF_PREFIX}/g" > ${BUILD}/sf-host.yaml
    cat ../tools/manage-sf/manage-sf.conf | sed "s/SF_PREFIX/${SF_PREFIX}/g" > ${BUILD}/manage-sf.conf
    # Fix jenkins for lxc
    sudo sed -i 's/^#*JAVA_ARGS.*/JAVA_ARGS="-Djava.awt.headless=true -Xmx256m"/g' /var/lib/debootstrap/install/D7-H.1.0.0/softwarefactory/etc/default/jenkins
    # Update puppet modules
    sudo mkdir -p /var/lib/debootstrap/install/D7-H.1.0.0/install-server/etc/puppet/{modules,manifests}
    sudo cp ../puppet/hiera.yaml /var/lib/debootstrap/install/D7-H.1.0.0/install-server/etc/puppet/
    sudo rsync -a ../puppet/modules/ /var/lib/debootstrap/install/D7-H.1.0.0/install-server/etc/puppet/modules/
    sudo rsync -a ../puppet/manifests/ /var/lib/debootstrap/install/D7-H.1.0.0/install-server/etc/puppet/manifests/
    # We alreay have puppetmaster IP, so we can generate cloudinit
    generate_cloudinit
    sudo ${EDEPLOY_LXC} --config ${BUILD}/sf-host.yaml restart || exit -1
    sf_postconfigure
elif [ "$1" == "stop" ]; then
    sudo ${EDEPLOY_LXC} --config ${BUILD}/sf-lxc.yaml stop
elif [ "$1" == "clean" ]; then
    sudo ${EDEPLOY_LXC} --config ${BUILD}/sf-lxc.yaml stop || echo
    rm -Rf ${BUILD} || echo
    # make sure all lxc are shutdown
    #for instance in $(sudo lxc-ls --active); do
    for instance in $(sudo lxc-ls); do
        #sudo lxc-stop --kill --name ${instance} || echo
        sudo lxc-stop --name ${instance} || echo
    done
else
    echo "usage: $0 [start|stop|clean]"
fi
