#!/bin/bash
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

BUILD=${BUILD:-../build}

# TODO: Should be moved in other place maybe a config file for bootstrap scripts ?
GERRIT_ADMIN=user1
GERRIT_ADMIN_MAIL=user1@example.com
GERRIT_ADMIN_PASSWORD=userpass

GERRIT_MYSQL_SECRET=''
REDMINE_MYSQL_SECRET=''
ETHERPAD_MYSQL_SECRET=''

#### Configuration generation
function new_build {
    rm -Rf ${BUILD}/
    mkdir ${BUILD}
    [ ! -d "${BUILD}/cloudinit" ] && mkdir ${BUILD}/cloudinit
    # puppetmaster cloudinit file can be used directly
    cat ../cloudinit/puppetmaster.cloudinit | sed "s/SF_PREFIX/${SF_PREFIX}/g" > ${BUILD}/cloudinit/puppetmaster.cloudinit
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

function gethostname_from_yaml {
    cat ${BUILD}/sf-host.yaml | grep "name: .*$1.*$" | cut -d: -f2 | sed 's/ *//g'
}

function getip_from_yaml {
    cat ${BUILD}/sf-host.yaml  | grep -A 1 -B 1 "name: $1$" | grep 'address' | cut -d: -f2 | sed 's/ *//g'
}

function getip_from_yaml_devstack {
    cat ${BUILD}/sf-host-tunneled.yaml  | grep -A 1 -B 1 "name: $1$" | grep 'address' | cut -d: -f2 | sed 's/ *//g'
}

function generate_random_pswd {
    echo `dd if=/dev/urandom bs=1 count=$1 2>/dev/null | base64 -w $1 | head -n1`
}

function generate_cloudinit {
    OUTPUT=${BUILD}/cloudinit
    puppetmaster_host=$(gethostname_from_yaml puppetmaster)
    PUPPETMASTER_IP=$(getip_from_yaml ${puppetmaster_host})
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    for i in ../cloudinit/*.cloudinit; do
        cat $i | sed -e "s#PUPPETMASTER#${PUPPETMASTER_IP}#g" -e "s/SF_PREFIX/${SF_PREFIX}/" > ${OUTPUT}/$(basename $i)
    done
    
    REDMINE_MYSQL_SECRET=$(generate_random_pswd 8)
    GERRIT_MYSQL_SECRET=$(generate_random_pswd 8)
    ETHERPAD_MYSQL_SECRET=$(generate_random_pswd 8)
    sed -i "s#REDMINE_MYSQL_SECRET#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/mysql.cloudinit
    sed -i "s#GERRIT_MYSQL_SECRET#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/mysql.cloudinit
    sed -i "s#ETHERPAD_MYSQL_SECRET#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/mysql.cloudinit
}

function generate_api_key() {
    out=""
    while [ ${#out} -lt 40 ];
        do
            out=$out`echo "obase=16; $RANDOM" | bc`
        done

    out=${out:0:40}
    echo $out | awk '{print tolower($0)}'
}

function generate_hiera {
    OUTPUT=${BUILD}/hiera
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    cp ../puppet/hiera/common.yaml ${OUTPUT}/common.yaml
    cp ../puppet/hiera/monit.yaml ${OUTPUT}/monit.yaml
    cp ../puppet/hiera/etherpad.yaml ${OUTPUT}/etherpad.yaml

    # Hosts
    echo -e "hosts:\n  localhost:\n    ip: 127.0.0.1" > ${OUTPUT}/hosts.yaml
    for role in $ROLES; do
        echo "  ${role}.pub:" >> ${OUTPUT}/hosts.yaml
        echo "    ip: $(getip_from_yaml ${role})" >> ${OUTPUT}/hosts.yaml
        echo "    host_aliases: [${role}, ${role}.pub]" >> ${OUTPUT}/hosts.yaml
        current_role=`echo "${role}" | sed 's/.*\(gerrit\|redmine\|jenkins\|mysql\|ldap\).*/\1/g'`
        sed -i "s#${current_role}_url:.*#${current_role}_url: ${role}#g" ${OUTPUT}/common.yaml
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
    sed -i "s#GERRIT_ADMIN_PASSWORD#${GERRIT_ADMIN_PASSWORD}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_MAIL#${GERRIT_ADMIN_MAIL}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_MYSQL_SECRET#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/gerrit.yaml

    # Gerrit other random tokens
    GERRIT_EMAIL_PK=$(generate_random_pswd 32)
    GERRIT_TOKEN_PK=$(generate_random_pswd 32)
    sed -i "s#GERRIT_EMAIL_PK#${GERRIT_EMAIL_PK}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_TOKEN_PK#${GERRIT_TOKEN_PK}#" ${OUTPUT}/gerrit.yaml

    # Gerrit Redmine API key
    REDMINE_API_KEY=$(generate_api_key)
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/gerrit.yaml

    # Redmine API key
    cat ../puppet/hiera/redmine.yaml | sed "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" > ${OUTPUT}/redmine.yaml
    sed -i "s#REDMINE_MYSQL_SECRET#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/redmine.yaml

    # Redmine Credencials ID
    # TODO: Will be randomly generated
    JENKINS_CREDS_ID="a6feb755-3493-4635-8ede-216127d31bb0"
    cat ../puppet/hiera/jenkins.yaml | sed "s#JENKINS_CREDS_ID#${JENKINS_CREDS_ID}#" > ${OUTPUT}/jenkins.yaml

    # Etherpad
    ETHERPAD_SESSION_KEY=$(generate_random_pswd 10)
    sed -i "s#SESSION_KEY#${ETHERPAD_SESSION_KEY}#" ${OUTPUT}/etherpad.yaml
    sed -i "s#ETHERPAD_MYSQL_SECRET#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/etherpad.yaml
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
        if [ "z`grep \"${role}$\" /etc/hosts`" != "z" ]; then
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
    gerrit_host=$(gethostname_from_yaml gerrit)
    if [ -n "$1" ]; then
        ip=$(getip_from_yaml_devstack $gerrit_host)
    else
        ip=$(getip_from_yaml $gerrit_host)
    fi
    _post_configuration_knownhosts "${gerrit_host}" $ip 29418
}

function _post_configuration_knownhosts {
    local role=$1
    local ip=$2
    local port=$3
    if [ "$port" != "22" ]; then
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$role]:$port" > /dev/null 2>&1 || echo
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$ip]:$port" > /dev/null 2>&1 || echo
    else
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$role" > /dev/null 2>&1 || echo
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$ip" > /dev/null 2>&1 || echo
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
    sed -i -e "s/SF_PREFIX/${SF_PREFIX}/g" ${OUTPUT}/hosts.yaml
}

function post_configuration_update_hiera {
    puppetmaster_host=$(gethostname_from_yaml puppetmaster)
    local ssh_port=22
    if [ -n "$1" ]; then
        let ssh_port=ssh_port+1024
    fi
    ssh root@$puppetmaster_host mkdir -p /etc/puppet/hiera/
    scp -P$ssh_port ${BUILD}/hiera/*.yaml root@$puppetmaster_host:/etc/puppet/hiera/
}

function post_configuration_ssh_keys {
    jenkins_host=$(gethostname_from_yaml jenkins)
    gerrit_host=$(gethostname_from_yaml gerrit)
    managesf_host=$(gethostname_from_yaml managesf)

    local ssh_port=22
    if [ -n "$1" ]; then
        let ssh_port=ssh_port+1024
    fi
    ssh -p$ssh_port root@$jenkins_host mkdir /var/lib/jenkins/.ssh/
    scp -P$ssh_port ${BUILD}/data/jenkins_rsa root@$jenkins_host:/var/lib/jenkins/.ssh/id_rsa
    ssh -p$ssh_port root@$jenkins_host chown -R jenkins /var/lib/jenkins/.ssh/
    ssh -p$ssh_port root@$jenkins_host chmod 400 /var/lib/jenkins/.ssh/id_rsa
    scp -P$ssh_port ${BUILD}/data/gerrit_service_rsa root@$gerrit_host:/home/gerrit/ssh_host_rsa_key
    scp -P$ssh_port ${BUILD}/data/gerrit_service_rsa.pub root@$gerrit_host:/home/gerrit/ssh_host_rsa_key.pub
    scp -p$ssh_port ${BUILD}/data/gerrit_admin_rsa root@$managesf_host:/var/www/managesf
    ssh -p$ssh_port root@$gerrit_host chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key
    ssh -p$ssh_port root@$gerrit_host chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key.pub
}

function post_configuration_jenkins_scripts {
    jenkins_host=$(gethostname_from_yaml jenkins)
    # Update jenkins slave scripts
    local ssh_port=22
    if [ -n "$1" ]; then
        let ssh_port=ssh_port+1024
    fi
    for host in "${jenkins_host}"; do
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
