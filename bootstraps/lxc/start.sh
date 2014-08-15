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

source ../functions.sh

DVER=D7
PVER=H
REL=${SF_REL:-0.9.0}
VERS=${DVER}-${PVER}.${REL}

SFCONFIGFILE=../sfconfig.yaml
DOMAIN=$(cat $SFCONFIGFILE | grep domain | cut -d' ' -f2)
SF_SUFFIX=${SF_SUFFIX:-$DOMAIN}
EDEPLOY_ROLES=${EDEPLOY_ROLES:-/var/lib/sf/roles/}
SSH_PUBKEY=${SSH_PUBKEY:-/home/ubuntu/.ssh/id_rsa.pub}
export SF_SUFFIX

ROLES="puppetmaster mysql redmine"
ROLES="$ROLES gerrit managesf jenkins commonservices"
ROLES="$ROLES slave"

EDEPLOY_LXC=/srv/edeploy-lxc/edeploy-lxc
CONFTEMPDIR=/tmp/lxc-conf
# Need to be select randomly
SSHPASS=heat
JENKINS_MASTER_URL=jenkins.${SF_SUFFIX}
JENKINS_USER_PASSWORD=$(generate_random_pswd 8)

function get_ip {
    grep -B 1 "name:[ \t]*$1" sf-lxc.yaml | head -1 | awk '{ print $2 }'
}

if [ -z "$1" ] || [ "$1" == "start" ]; then
    [ ! -d ${CONFTEMPDIR} ] && mkdir -p ${CONFTEMPDIR}
    cp sf-lxc.yaml $CONFTEMPDIR
    cp ../cloudinit/* $CONFTEMPDIR
    jenkins_ip=`get_ip jenkins`
    # Complete the sf-lxc template used by edeploy-lxc tool
    sed -i "s/SF_SUFFIX/${SF_SUFFIX}/g" ${CONFTEMPDIR}/sf-lxc.yaml
    sed -i "s/VERS/${VERS}/g" ${CONFTEMPDIR}/sf-lxc.yaml
    sed -i "s#CIPATH#${CONFTEMPDIR}#g" ${CONFTEMPDIR}/sf-lxc.yaml
    sed -i "s#SSH_PUBKEY#${SSH_PUBKEY}#g" ${CONFTEMPDIR}/sf-lxc.yaml
    sed -i "s#EDEPLOY_ROLES#${EDEPLOY_ROLES}#g" ${CONFTEMPDIR}/sf-lxc.yaml
    # Complete jenkins slave cloudinit 
    sed -i "s/JENKINS_MASTER_URL/${JENKINS_MASTER_URL}/g" ${CONFTEMPDIR}/slave.cloudinit
    sed -i "s/JENKINS_USER_PASSWORD/${JENKINS_USER_PASSWORD}/g" ${CONFTEMPDIR}/slave.cloudinit
    sed -i "s/JENKINS_IP/${jenkins_ip}/g" ${CONFTEMPDIR}/slave.cloudinit
    # Complete all the cloudinit templates
    sed -i "s/SF_SUFFIX/${SF_SUFFIX}/g" ${CONFTEMPDIR}/*.cloudinit
    sed -i "s/SSHPASS/${SSHPASS}/g" ${CONFTEMPDIR}/*.cloudinit
    sfconfigcontent=`cat $SFCONFIGFILE | base64 -w 0`
    sed -i "s|SFCONFIGCONTENT|${sfconfigcontent}|" $CONFTEMPDIR/puppetmaster.cloudinit
    for r in mysql redmine gerrit managesf jenkins commonservices; do
        ip=`get_ip $r`
        sed -i "s/${r}_host/$ip/g" ${CONFTEMPDIR}/puppetmaster.cloudinit
    done
    ip=`get_ip puppetmaster`
    sed -i "s/JENKINS_USER_PASSWORD/${JENKINS_USER_PASSWORD}/" ${CONFTEMPDIR}/puppetmaster.cloudinit
    sed -i "s/MY_PRIV_IP=.*/MY_PRIV_IP=$ip/" ${CONFTEMPDIR}/puppetmaster.cloudinit
    # Fix jenkins for lxc
    sudo sed -i 's/^#*JAVA_ARGS.*/JAVA_ARGS="-Djava.awt.headless=true -Xmx256m"/g' \
        ${EDEPLOY_ROLES}/install/${DVER}-${PVER}.${REL}/softwarefactory/etc/default/jenkins
    echo "Now running edeploy-lxc"
    sudo ${EDEPLOY_LXC} --config ${CONFTEMPDIR}/sf-lxc.yaml stop > /dev/null || exit -1

    if [ -e "/mnt/lxc/puppetmaster/etc/puppet/" ]; then
        sudo sh -c "echo 'lxc.mount.entry =  /mnt/lxc/puppetmaster/etc/puppet/ /var/lib/lxc/puppetmaster/rootfs/etc/puppet none bind,create=dir 0 0' >  /var/lib/lxc/puppetmaster.config"
    else
        rm -f /var/lib/lxc/puppetmaster.config
    fi
 
    if [ -e "/mnt/lxc/puppetmaster/root/puppet-bootstrapper" ]; then
        sudo sh -c "echo 'lxc.mount.entry =  /mnt/lxc/puppetmaster/root/puppet-bootstrapper /var/lib/lxc/puppetmaster/rootfs/root/puppet-bootstrapper none bind,create=dir 0 0' >>  /var/lib/lxc/puppetmaster.config"
    else
        rm -f /var/lib/lxc/puppetmaster.config
    fi

    if [ -e "/mnt/lxc/mysql/mysql/" ]; then
        sudo sh -c "echo 'lxc.mount.entry = /mnt/lxc/mysql/mysql/ /var/lib/lxc/mysql/rootfs/var/lib/mysql none bind,create=dir 0 0' >  /var/lib/lxc/mysql.config"
    else
        rm -f /var/lib/lxc/mysql.config
    fi

    if [ -e "/mnt/lxc/gerrit/home/gerrit/site_path/git/" ]; then
        # Path must exist before mounting, otherwise LXC fails
        sudo mkdir -p ${EDEPLOY_ROLES}/install/${VERS}/softwarefactory/home/gerrit/site_path/git
        sudo sh -c "echo 'lxc.mount.entry = /mnt/lxc/gerrit/home/gerrit/site_path/git/ /var/lib/lxc/gerrit/rootfs/home/gerrit/site_path/git none bind,create=dir 0 0' >  /var/lib/lxc/gerrit.config"
    else
        rm -f /var/lib/lxc/gerrit.config
    fi

    if [ -e "/mnt/lxc/jenkins/var/lib/jenkins/jobs/" ]; then
        # Path must exist before mounting, otherwise LXC fails
        sudo mkdir -p ${EDEPLOY_ROLES}/install/${VERS}/softwarefactory/var/lib/jenkins/jobs/
        sudo sh -c "echo 'lxc.mount.entry = /mnt/lxc/jenkins/var/lib/jenkins/jobs/ /var/lib/lxc/jenkins/rootfs/var/lib/jenkins/jobs none bind,create=dir 0 0' >  /var/lib/lxc/jenkins.config"
    else
        rm -f /var/lib/lxc/jenkins.config
    fi

    # Let's add a default nameserver
    nameserver=`grep nameserver /etc/resolv.conf`
    sed -i -e "s/NAMESERVER/${nameserver}/g" ${CONFTEMPDIR}/*.cloudinit

    sudo ${EDEPLOY_LXC} --config ${CONFTEMPDIR}/sf-lxc.yaml start > /dev/null || exit -1
elif [ "$1" == "stop" ]; then
    [ -f "${CONFTEMPDIR}/sf-lxc.yaml" ] && sudo ${EDEPLOY_LXC} --config ${CONFTEMPDIR}/sf-lxc.yaml stop
elif [ "$1" == "clean" ]; then
    [ -f "${CONFTEMPDIR}/sf-lxc.yaml" ] && sudo ${EDEPLOY_LXC} --config ${CONFTEMPDIR}/sf-lxc.yaml stop || echo
    rm -Rf ${CONFTEMPDIR} || echo
    # make sure all lxc are shutdown
    #for instance in $(sudo lxc-ls --active); do
    for instance in $(sudo lxc-ls); do
        # We need to kill first, else it stop because "sf-mysql is running"
        sudo lxc-stop --kill --name ${instance} || echo
        sudo lxc-destroy --name ${instance} || echo
    done
elif [ "$1" == "seed" ]; then
        sudo mkdir -p /mnt/lxc/puppetmaster/etc/puppet/
        sudo rsync -av /var/lib/lxc/puppetmaster/rootfs/etc/puppet/ /mnt/lxc/puppetmaster/etc/puppet/
        sudo mkdir -p /mnt/lxc/puppetmaster/root/puppet-bootstrapper/
        sudo rsync -av /var/lib/lxc/puppetmaster/rootfs/root/puppet-bootstrapper/ /mnt/lxc/puppetmaster/root/puppet-bootstrapper/
        sudo mkdir -p /mnt/lxc/mysql/mysql/
        sudo rsync -av /var/lib/lxc/mysql/rootfs/var/lib/mysql/ /mnt/lxc/mysql/mysql/
        sudo mkdir -p /mnt/lxc/gerrit/home/gerrit/site_path/git/
        sudo rsync -av /var/lib/lxc/gerrit/rootfs/home/gerrit/site_path/git/ /mnt/lxc/gerrit/home/gerrit/site_path/git/
        sudo mkdir -p /mnt/lxc/jenkins/var/lib/jenkins/jobs/
        sudo rsync -av /var/lib/lxc/jenkins/rootfs/var/lib/jenkins/jobs/ /mnt/lxc/jenkins/var/lib/jenkins/jobs/
else
    echo "usage: $0 [start|stop|clean]"
fi

exit 0
