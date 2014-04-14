#!/bin/bash
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

set -x
set -e

SF_PREFIX=${SF_PREFIX:-sf}
EDEPLOY_ROLES=${EDEPLOY_ROLES:-/var/lib/debootstrap}
export SF_PREFIX

. ../function.sh

ROLES="${SF_PREFIX}-puppetmaster ${SF_PREFIX}-ldap ${SF_PREFIX}-mysql ${SF_PREFIX}-redmine ${SF_PREFIX}-jenkins ${SF_PREFIX}-gerrit"
EDEPLOY_LXC=/srv/edeploy-lxc/edeploy-lxc

if [ -z "$1" ] || [ "$1" == "start" ]; then
    new_build
    # Fix SF_PREFIX bootstrap && manage-sf configuration
    cat sf-lxc.yaml | sed "s/SF_PREFIX/${SF_PREFIX}/g" > ${BUILD}/sf-host.yaml
    sed -i "s#EDEPLOY_ROLES#${EDEPLOY_ROLES}#g" ${BUILD}/sf-host.yaml
    # Fix jenkins for lxc
    sudo sed -i 's/^#*JAVA_ARGS.*/JAVA_ARGS="-Djava.awt.headless=true -Xmx256m"/g' $EDEPLOY_ROLES/install/D7-H.1.0.0/softwarefactory/etc/default/jenkins
    # Update puppet modules
    sudo mkdir -p $EDEPLOY_ROLES/install/D7-H.1.0.0/install-server/etc/puppet/{modules,manifests}
    sudo cp ../puppet/hiera.yaml $EDEPLOY_ROLES/install/D7-H.1.0.0/install-server/etc/puppet/
    sudo rsync -a ../puppet/modules/ $EDEPLOY_ROLES/install/D7-H.1.0.0/install-server/etc/puppet/modules/
    sudo rsync -a ../puppet/manifests/ $EDEPLOY_ROLES/install/D7-H.1.0.0/install-server/etc/puppet/manifests/
    # We alreay have puppetmaster IP, so we can generate cloudinit
    generate_cloudinit
    sudo ${EDEPLOY_LXC} --config ${BUILD}/sf-host.yaml restart || exit -1
    sf_postconfigure
elif [ "$1" == "stop" ]; then
    [ -f "${BUILD}/sf-host.yaml" ] && sudo ${EDEPLOY_LXC} --config ${BUILD}/sf-host.yaml stop
elif [ "$1" == "clean" ]; then
    [ -f "${BUILD}/sf-host.yaml" ] && sudo ${EDEPLOY_LXC} --config ${BUILD}/sf-host.yaml stop || echo
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
