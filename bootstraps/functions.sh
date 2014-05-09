#!/bin/bash
#
# copyright (c) 2014 enovance sas <licensing@enovance.com>
#
# licensed under the apache license, version 2.0 (the "license"); you may
# not use this file except in compliance with the license. you may obtain
# a copy of the license at
#
# http://www.apache.org/licenses/license-2.0
#
# unless required by applicable law or agreed to in writing, software
# distributed under the license is distributed on an "as is" basis, without
# warranties or conditions of any kind, either express or implied. see the
# license for the specific language governing permissions and limitations
# under the license.

set -e
set -x

function getip_from_yaml {
    cat ../hosts.yaml  | grep -A 1 "^  $1" | grep 'ip:' | cut -d: -f2 | sed 's/ *//g'
}

function generate_random_pswd {
    # The sed character replacement makes the base64-string URL safe; for example required by lodgeit
    echo `dd if=/dev/urandom bs=1 count=$1 2>/dev/null | base64 -w $1 | head -n1 | sed -e 's#/#_#g;s#\+#-#g'`
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

function generate_hieras {
    OUTPUT=${BUILD}/hiera
    mkdir -p ${OUTPUT}
    
    cp puppet/hiera/* ${OUTPUT}/

    for role in $ROLES; do
        current_role=`echo "${role}" | sed 's/.*\(gerrit\|redmine\|jenkins\|mysql\|ldap\|managesf\).*/\1/g'`
        sed -i "s#${current_role}_url:.*#${current_role}_url: ${role}#g" ${OUTPUT}/common.yaml
    done

    # MySQL password for services
    REDMINE_MYSQL_SECRET=$(generate_random_pswd 8)
    GERRIT_MYSQL_SECRET=$(generate_random_pswd 8)
    ETHERPAD_MYSQL_SECRET=$(generate_random_pswd 8)
    LODGEIT_MYSQL_SECRET=$(generate_random_pswd 8)
    sed -i "s#REDMINE_SQL_PWD#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml
    sed -i "s#GERRIT_SQL_PWD#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml
    sed -i "s#ETHERPAD_SQL_PWD#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml
    sed -i "s#LODGEIT_SQL_PWD#${LODGEIT_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml

    # Default authorized ssh keys on each node
    JENKINS_PUB="$(cat ${OUTPUT}/../data/jenkins_rsa.pub | cut -d' ' -f2)"
    sed -i "s#JENKINS_PUB_KEY#${JENKINS_PUB}#" ${OUTPUT}/ssh.yaml
    SERVICE_PUB="$(cat ${OUTPUT}/../data/service_rsa.pub | cut -d' ' -f2)"
    sed -i "s#SERVICE_PUB_KEY#${SERVICE_PUB}#" ${OUTPUT}/ssh.yaml
    
    # Jenkins part
    # TODO: Must be randomly generated
    JENKINS_CREDS_ID="a6feb755-3493-4635-8ede-216127d31bb0"
    sed -i "s#JENKINS_CREDS_ID#${JENKINS_CREDS_ID}#" ${OUTPUT}/jenkins.yaml
    sed -i "s#LDAP_ADMIN_DN#${LDAP_ADMIN_DN}#" ${OUTPUT}/jenkins.yaml
    # using printf instead of echo along with base64 encoding
    # as echo was not giving correct values
    sed -i "s#LDAP_ADMIN_PASSWORD_BASE64#$(printf ${LDAP_ADMIN_PASSWORD} | base64)#" ${OUTPUT}/jenkins.yaml
    sed -i "s#JENKINS_ADMIN_NAME#${JENKINS_ADMIN}#" ${OUTPUT}/jenkins.yaml

    # Redmine part
    REDMINE_API_KEY=$(generate_api_key)
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/redmine.yaml
    sed -i "s#REDMINE_MYSQL_SECRET#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/redmine.yaml
    sed -i "s#REDMINE_ADMIN_NAME#${REDMINE_ADMIN}#" ${OUTPUT}/redmine.yaml
    
    # Gerrit part
    GERRIT_SERV_PUB="$(cat ${OUTPUT}/../data/gerrit_service_rsa.pub | cut -d' ' -f2)"
    GERRIT_ADMIN_PUB_KEY="$(cat ${OUTPUT}/../data/gerrit_admin_rsa.pub | cut -d' ' -f2)"
    GERRIT_EMAIL_PK=$(generate_random_pswd 32)
    GERRIT_TOKEN_PK=$(generate_random_pswd 32)
    sed -i "s#GERRIT_SERV_PUB_KEY#ssh-rsa ${GERRIT_SERV_PUB}#" ${OUTPUT}/gerrit.yaml
    # Gerrit Jenkins pub key
    sed -i "s#JENKINS_PUB_KEY#ssh-rsa ${JENKINS_PUB}#" ${OUTPUT}/gerrit.yaml
    # Gerrit Admin pubkey,mail,login
    sed -i "s#GERRIT_ADMIN_PUB_KEY#ssh-rsa ${GERRIT_ADMIN_PUB_KEY}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_NAME#${GERRIT_ADMIN}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_PASSWORD#${GERRIT_ADMIN_PASSWORD}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_MAIL#${GERRIT_ADMIN_MAIL}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_MYSQL_SECRET#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_EMAIL_PK#${GERRIT_EMAIL_PK}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_TOKEN_PK#${GERRIT_TOKEN_PK}#" ${OUTPUT}/gerrit.yaml
    
    # Etherpad part
    ETHERPAD_SESSION_KEY=$(generate_random_pswd 10)
    sed -i "s#SESSION_KEY#${ETHERPAD_SESSION_KEY}#" ${OUTPUT}/etherpad.yaml
    sed -i "s#ETHERPAD_MYSQL_SECRET#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/etherpad.yaml

    # Lodgeit/Paste part
    LODGEIT_SESSION_KEY=$(generate_random_pswd 10)
    sed -i "s#SESSION_KEY#${LODGEIT_SESSION_KEY}#" ${OUTPUT}/lodgeit.yaml
    sed -i "s#LODGEIT_MYSQL_SECRET#${LODGEIT_MYSQL_SECRET}#" ${OUTPUT}/lodgeit.yaml
}

function wait_all_nodes {
    local port=22
    for role in $ROLES; do
        ip=$(getip_from_yaml $role)
        echo $role $ip
        scan_and_configure_knownhosts "$role" $ip $port
    done
}

function scan_and_configure_knownhosts {
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

function generate_serverspec {
    OUTPUT=${BUILD}/serverspec
    mkdir -p ${OUTPUT}
    cp serverspec/hosts.yaml.tpl ${OUTPUT}/hosts.yaml
    sed -i -e "s/SF_PREFIX/${SF_PREFIX}/g" ${OUTPUT}/hosts.yaml
}

function generate_keys {
    OUTPUT=${BUILD}/data
    mkdir -p ${OUTPUT}
    # Service key is used to allow puppetmaster root to
    # connect on other node as root
    ssh-keygen -N '' -f ${OUTPUT}/service_rsa
    cp ${OUTPUT}/service_rsa /root/.ssh/id_rsa
    ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_service_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_admin_rsa
}

function prepare_etc_puppet {
    DATA=${BUILD}/data
    mkdir -p /etc/puppet/environments/sf
    mkdir -p /etc/puppet/hiera/sf
    cp -Rf puppet/manifests /etc/puppet/environments/sf
    cp -Rf puppet/modules /etc/puppet/environments/sf
    cp puppet/hiera.yaml /etc/puppet/
    cp build/hiera/* /etc/puppet/hiera/sf
    cp ../hosts.yaml /etc/puppet/hiera/sf
    cp $DATA/jenkins_rsa /etc/puppet/environments/sf/modules/jenkins/files/
    cp $DATA/jenkins_rsa /etc/puppet/environments/sf/modules/zuul/files/
    cp $DATA/gerrit_admin_rsa /etc/puppet/environments/sf/modules/jenkins/files/
    cp $DATA/gerrit_service_rsa /etc/puppet/environments/sf/modules/gerrit/files/
    cp $DATA/gerrit_service_rsa.pub /etc/puppet/environments/sf/modules/gerrit/files/
    cp $DATA/gerrit_admin_rsa /etc/puppet/environments/sf/modules/managesf/files/
    cp $DATA/gerrit_admin_rsa /etc/puppet/environments/sf/modules/jjb/files/
    chown -R puppet:puppet /etc/puppet/environments/sf
    chown -R puppet:puppet /etc/puppet/hiera/sf
    chown -R puppet:puppet /var/lib/puppet
}

function start_puppetmaster_service {
    /etc/init.d/puppetmaster restart
}

function run_puppet_agent {
    puppet agent --test --environment sf || true
    /etc/init.d/puppet start
}

function trigger_puppet_apply {
    local puppetmaster_ip=$(getip_from_yaml $SF_PREFIX-puppetmaster)
    local ssh_port=22
    MROLES=$(echo $ROLES | sed s/$SF_PREFIX-puppetmaster//)
    for role in ${MROLES}; do
        echo " [+] ${role}"
        sshpass -p "$TEMP_SSH_PWD" ssh -p$ssh_port root@${role} sed -i "s/puppetmaster-ip-template/$puppetmaster_ip/" /etc/hosts
        # The Puppet run will deactivate the temporary root password
        sshpass -p "$TEMP_SSH_PWD" ssh -p$ssh_port root@${role} "puppet agent --test --environment sf || true; /etc/init.d/puppet start"
        sleep 5
    done
}
