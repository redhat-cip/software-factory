#!/bin/bash

BUILD=${BUILD:-../build}

# TODO: Should be moved in other place maybe a config file for bootstrap scripts ?
GERRIT_ADMIN=fabien.boucher
GERRIT_ADMIN_MAIL=fabien.boucher@enovance.com

#### Configuration generation
function new_build {
    rm -Rf ${BUILD}/
    mkdir ${BUILD}
    [ ! -d "${BUILD}/cloudinit" ] && mkdir ${BUILD}/cloudinit
    # puppetmaster cloudinit file can be used directly
    cp ../cloudinit/puppetmaster.cloudinit \
        ${BUILD}/cloudinit/puppetmaster.cloudinit
    echo "hosts:" > ${BUILD}/sf-host.yaml
}

function putip_to_yaml {
    cat << EOF >> ${BUILD}/sf-host.yaml
  -
    name: $1
    address: $2
EOF
}

function putip_to_yaml_devstack {
    cat << EOF >> ${BUILD}/sf-host-tunneled.yaml
  -
    name: $1
    address: $2
EOF
}

function getip_from_yaml {
    cat ${BUILD}/sf-host.yaml  | grep -A 1 -B 1 "name: $1$" | grep 'address' | cut -d: -f2 | sed 's/ *//g'
}

function getip_from_yaml_devstack {
    cat ${BUILD}/sf-host-tunneled.yaml  | grep -A 1 -B 1 "name: $1$" | grep 'address' | cut -d: -f2 | sed 's/ *//g'
}

function generate_cloudinit {
    OUTPUT=${BUILD}/cloudinit
    PUPPETMASTER_IP=$(getip_from_yaml sf-puppetmaster)
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    for i in ../cloudinit/*.cloudinit; do
        cat $i | sed "s#PUPPETMASTER#${PUPPETMASTER_IP}#g" > ${OUTPUT}/$(basename $i)
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
        echo "    ip: $(getip_from_yaml ${role})" >> ${OUTPUT}/hosts.yaml
        echo "    host_aliases: [${role}, ${role}.pub]" >> ${OUTPUT}/hosts.yaml
    done

    # Jenkins ssh key
    JENKINS_PUB="$(cat ${OUTPUT}/../data/jenkins_rsa.pub | cut -d' ' -f2)"
    cat ../puppet/hiera/ssh.yaml | sed "s#JENKINS_PUB_KEY#${JENKINS_PUB}#" > ${OUTPUT}/ssh.yaml

    # Gerrit service key
    GERRIT_SERV_PUB="$(cat ${OUTPUT}/../data/gerrit_service_rsa.pub | cut -d' ' -f2)"
    cat ../puppet/hiera/gerrit.yaml | sed "s#GERRIT_SERV_PUB_KEY#ssh-rsa ${GERRIT_SERV_PUB}#" > ${OUTPUT}/gerrit.yaml

    # Gerrit Jenkins pub key
    sed -i "s#JENKINS_PUB_KEY#ssh-rsa ${JENKINS_PUB}#" ${OUTPUT}/gerrit.yaml

    # Gerrit Admin pubkey,mail,login
    GERRIT_ADMIN_PUB_KEY="$(cat ${OUTPUT}/../data/gerrit_admin_rsa.pub | cut -d' ' -f2)"
    sed -i "s#GERRIT_ADMIN_PUB_KEY#ssh-rsa ${GERRIT_ADMIN_PUB_KEY}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_NAME#${GERRIT_ADMIN}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_MAIL#${GERRIT_ADMIN_MAIL}#" ${OUTPUT}/gerrit.yaml

    # Gerrit Redmine API key
    # TODO Will be randomly generated
    REDMINE_API_KEY="7f094d4e3e327bbd3f67279c95c193825e48f59e"
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/gerrit.yaml

    # Redmine API key
    cat ../puppet/hiera/redmine.yaml | sed "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" > ${OUTPUT}/redmine.yaml

    # Redmine Credencials ID
    # TODO: Will be randomly generated
    JENKINS_CREDS_ID="a6feb755-3493-4635-8ede-216127d31bb0"
    cat ../puppet/hiera/jenkins.yaml | sed "s#JENKINS_CREDS_ID#${JENKINS_CREDS_ID}#" > ${OUTPUT}/jenkins.yaml
}

function generate_keys {
    OUTPUT=${BUILD}/data
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_service_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_admin_rsa
}

#### Post configuration
function post_configuration_etc_hosts {
    # Make sure /etc/hosts is up-to-date
    for role in ${ROLES}; do
        if [ -z "$1" ]; then
            HOST_LINE="$(getip_from_yaml ${role}) ${role}"
        else
            HOST_LINE="$(getip_from_yaml_devstack ${role}) ${role}"
        fi
        grep "${role}$" /etc/hosts > /dev/null
        if [ $? == 0 ]; then
            cat /etc/hosts | grep -v "${role}$" | sudo tee /etc/hosts.new > /dev/null
            sudo mv /etc/hosts.new /etc/hosts
        fi
        echo ${HOST_LINE} | sudo tee -a /etc/hosts > /dev/null
    done
}


function post_configuration_knownhosts {
    local port=22
    if [ -n "$1" ]; then
        let port=port+1024
    fi
    for role in $ROLES; do
        if [ -n "$1" ]; then
            ip=$(getip_from_yaml_devstack $role)
        else
            ip=$(getip_from_yaml $role)
        fi
        _post_configuration_knownhosts "$role" $ip $port
    done
}

function post_configuration_gerrit_knownhosts {
    if [ -n "$1" ]; then
        ip=$(getip_from_yaml_devstack sf-gerrit)
    else
        ip=$(getip_from_yaml sf-gerrit)
    fi
    _post_configuration_knownhosts "sf-gerrit" $ip 29418
}

function _post_configuration_knownhosts {
    local role=$1
    local ip=$2
    local port=$3
    if [ "$port" != "22" ]; then
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$role]:$port" > /dev/null 2>&1
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$ip]:$port" > /dev/null 2>&1
    else
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$role" > /dev/null 2>&1
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$ip" > /dev/null 2>&1
    fi
    RETRIES=0
    echo " [+] Starting ssh-keyscan on $role:$port"
    while true; do
        KEY=`ssh-keyscan -p $port $role 2> /dev/null`
        if [ "$KEY" != ""  ]; then
                # fix ssh-keyscan bug for 2 ssh server on different port
                if [ "$port" != "22" ]; then
                    ssh-keyscan -p $port $role 2> /dev/null | sed "s/$role/[$role]:$port,[$ip]:$port/" >> "$HOME/.ssh/known_hosts"
                else
                    ssh-keyscan $role 2> /dev/null | sed "s/$role/$role,$ip/" >> "$HOME/.ssh/known_hosts"
                fi
                echo "  -> $role:$port is up!"
                break
        fi

        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && break
        echo "  [E] ssh-keyscan on $role:$port failed, will retry in 5 seconds (attempt $RETRIES/40)"
        sleep 10
    done
}

function post_configuration_puppet_apply {
    echo "[+] Running one last puppet agent"
    local ssh_port=22
    if [ -n "$1" ]; then
        let ssh_port=ssh_port+1024
    fi
    for role in ${ROLES}; do
        echo " [+] ${role}"
        ssh -p$ssh_port root@${role} puppet agent --test || echo "TODO: fix puppet agent failure"
    done
}

function generate_serverspec {
    OUTPUT=${BUILD}/serverspec
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    cp ../serverspec/hosts.yaml.tpl ${OUTPUT}/hosts.yaml
    for role in ${ROLES}; do
        if [ -z "$1" ]; then
            ip_role=$(getip_from_yaml ${role})
        else
            ip_role=$(getip_from_yaml_devstack ${role})
        fi
        sed -i -e "s/${role}_ip/$ip_role/g" ${OUTPUT}/hosts.yaml
    done
}

function post_configuration_update_hiera {
    local ssh_port=22
    if [ -n "$1" ]; then
        let ssh_port=ssh_port+1024
    fi
    scp -P$ssh_port ${BUILD}/hiera/*.yaml root@sf-puppetmaster:/etc/puppet/hiera/
}

function post_configuration_ssh_keys {
    local ssh_port=22
    if [ -n "$1" ]; then
        let ssh_port=ssh_port+1024
    fi
    ssh -p$ssh_port root@sf-jenkins mkdir /var/lib/jenkins/.ssh/
    scp -P$ssh_port ${BUILD}/data/jenkins_rsa root@sf-jenkins:/var/lib/jenkins/.ssh/id_rsa
    ssh -p$ssh_port root@sf-jenkins chown -R jenkins /var/lib/jenkins/.ssh/
    ssh -p$ssh_port root@sf-jenkins chmod 400 /var/lib/jenkins/.ssh/id_rsa
    scp -P$ssh_port ${BUILD}/data/gerrit_service_rsa root@sf-gerrit:/home/gerrit/ssh_host_rsa_key
    scp -P$ssh_port ${BUILD}/data/gerrit_service_rsa.pub root@sf-gerrit:/home/gerrit/ssh_host_rsa_key.pub
    ssh -p$ssh_port root@sf-gerrit chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key
    ssh -p$ssh_port root@sf-gerrit chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key.pub
}

function post_configuration_jenkins_scripts {
    # Update jenkins slave scripts
    local ssh_port=22
    if [ -n "$1" ]; then
        let ssh_port=ssh_port+1024
    fi
    for host in "sf-jenkins" "sf-jenkins-slave01" "sf-jenkins-slave02"; do
        ssh -p$ssh_port root@${host} mkdir -p /usr/local/jenkins/slave_scripts/
        scp -P$ssh_port ../data/jenkins_slave_scripts/* root@${host}:/usr/local/jenkins/slave_scripts/
    done
}

function sf_postconfigure {
    # ${BUILD}/sf-host.yaml must be present and filled with roles ip
    # devstack (just a flag) is used by the boostrap script for Openstack in
    # case of a devstack deployment (we create a tunnel from this host
    # to the floating IP inside the devstack).
    local devstack=$1
    generate_serverspec $devstack
    generate_keys
    generate_hiera
    post_configuration_etc_hosts $devstack
    post_configuration_knownhosts $devstack
    post_configuration_ssh_keys $devstack
    post_configuration_update_hiera $devstack
    post_configuration_puppet_apply $devstack
    post_configuration_jenkins_scripts $devstack
    post_configuration_gerrit_knownhosts $devstack
}
