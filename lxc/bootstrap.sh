#!/bin/bash

BUILD="../build"
ROLES="puppetmaster mysql ldap jenkins gerrit jenkins-slave"
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
        echo "  sf-${role}:" >> ${OUTPUT}/hosts.yaml
        echo "    ip: $(getip_from_lxcyaml ${role})" >> ${OUTPUT}/hosts.yaml
    done

    # Jenkins ssh key
    JENKINS_PUB="$(cat ${OUTPUT}/../data/jenkins_rsa.pub | cut -d' ' -f2)"
    cat ../puppet/hiera/ssh.yaml | sed "s#JENKINS_PUB_KEY#${JENKINS_PUB}#" > ${OUTPUT}/ssh.yaml
    
    # Gerrit service key
    GERRIT_SERV_PUB="$(cat ${OUTPUT}/../data/gerrit_service_rsa.pub | cut -d' ' -f2)"
    cat ../puppet/hiera/gerrit.yaml | sed "s#GERRIT_SERV_PUB_KEY#ssh-rsa ${GERRIT_SERV_PUB}#" > ${OUTPUT}/gerrit.yaml

    # Gerrit Jenkins pub key
    sed -i "s#JENKINS_PUB_KEY#ssh-rsa ${JENKINS_PUB}#" ${OUTPUT}/gerrit.yaml

    # Gerrit Redmine API key
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/gerrit.yaml

    # Redmine API key
    cat ../puppet/hiera/redmine.yaml | sed "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" > ${OUTPUT}/redmine.yaml
}

function generate_keys {
    OUTPUT=${BUILD}/data
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_service_rsa
    # TODO Will be randomly generated
    REDMINE_API_KEY="7f094d4e3e327bbd3f67279c95c193825e48f59e"
}

function post_configuration_etc_hosts {
    # Make sure /etc/hosts is up-to-date
    for role in ${ROLES}; do
        HOST_LINE="$(getip_from_lxcyaml ${role}) sf-${role}"
        grep sf-${role} /etc/hosts > /dev/null
        if [ $? == 0 ]; then
            sudo sed -i "s#^.*sf-${role}.*#${HOST_LINE}#" /etc/hosts
        else
            echo ${HOST_LINE} | sudo tee -a /etc/hosts > /dev/null
        fi
    done
}

function post_configuration_knownhosts {
    # Update known_hosts file
    echo "[+] Update local knownhosts file"
    for role in ${ROLES}; do
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R sf-${role} > /dev/null 2>&1
        RETRIES=0
        echo " [+] Starting ssh-keyscan on sf-${role}"
        while true; do
            KEY=`ssh-keyscan sf-${role} 2> /dev/null`
            if [ "$KEY" != ""  ]; then
                echo $KEY >> "$HOME/.ssh/known_hosts"
                echo "  -> sf-${role} is up!"
                break
            fi

            let RETRIES=RETRIES+1
            [ "$RETRIES" == "6" ] && break
            echo "  [E] ssh-keyscan on sf-${role} failed, will retry in 5 seconds"
            sleep 10
        done
    done
}

function post_configuration_puppet_apply {
    echo "[+] Running one last puppet agent"
    for role in ${ROLES}; do
        echo " [+] sf-${role}"
        ssh root@sf-${role} puppet agent --test
    done
}

function generate_all {
    generate_cloudinit
    generate_keys
    generate_hiera
}

if [ -z "$1" ] || [ "$1" == "start" ]; then
    generate_all
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml restart
    sudo scp ${BUILD}/hiera/*.yaml /var/lib/lxc/puppetmaster/rootfs/etc/puppet/hiera/
    sudo scp ${BUILD}/data/gerrit_service_rsa /var/lib/lxc/gerrit/rootfs/home/gerrit/ssh_host_rsa_key
    sudo scp ${BUILD}/data/gerrit_service_rsa.pub /var/lib/lxc/gerrit/rootfs/home/gerrit/ssh_host_rsa_key.pub
    sudo chroot /var/lib/lxc/gerrit/rootfs chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key
    sudo chroot /var/lib/lxc/gerrit/rootfs chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key.pub
    post_configuration_etc_hosts
    post_configuration_knownhosts
    post_configuration_puppet_apply
elif [ "$1" == "generate" ]; then
    generate_all
elif [ "$1" == "stop" ]; then
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml stop
elif [ "$1" == "clean" ]; then
    sudo ${EDEPLOY_LXC} --config sf-lxc.yaml stop
    rm -Rf ${BUILD}/*
else
    echo "usage: $0 [start|stop|clean]"
fi
