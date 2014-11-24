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

ROLES="puppetmaster"
ROLES="$ROLES mysql"
ROLES="$ROLES redmine"
ROLES="$ROLES gerrit"
ROLES="$ROLES managesf"
ROLES="$ROLES jenkins"
ROLES="$ROLES slave"

PUPPETIZED_ROLES=$(echo $ROLES | sed -e s/puppetmaster// -e s/slave//)

SFTMP=/tmp/sf-conf/
SFCONFIGFILE=$SFTMP/sfconfig.yaml

function hash_password {
    python -c "import crypt, random, string; salt = '\$6\$' + ''.join(random.choice(string.letters + string.digits) for _ in range(16)) + '\$'; print crypt.crypt('$1', salt)"
}

function generate_sfconfig {
    [ -d $SFTMP ] && rm -Rf $SFTMP
    mkdir $SFTMP
    cp ../sfconfig.yaml $SFCONFIGFILE

    # Set and generated admin password
    DEFAULT_ADMIN_USER=$(cat ../sfconfig.yaml | grep '^admin_name:' | awk '{ print $2 }')
    DEFAULT_ADMIN_PASSWORD=$(cat ../sfconfig.yaml | grep '^admin_password:' | awk '{ print $2 }')
    ADMIN_USER=${ADMIN_USER:-${DEFAULT_ADMIN_USER}}
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-${DEFAULT_ADMIN_PASSWORD}}
    ADMIN_PASSWORD_HASHED=$(hash_password "${ADMIN_PASSWORD}")
    sed -i "s/^admin_name:.*/admin_name: ${ADMIN_USER}/" /tmp/sf-conf/sfconfig.yaml
    sed -i "s/^admin_password:.*/admin_password: ${ADMIN_PASSWORD}/" /tmp/sf-conf/sfconfig.yaml
    echo "admin_password_hashed: \"${ADMIN_PASSWORD_HASHED}\"" >> /tmp/sf-conf/sfconfig.yaml
}

function getip_from_yaml {
    cat ../hosts.yaml  | grep -A 1 "^  $1" | grep 'ip:' | cut -d: -f2 | sed 's/ *//g'
}

function generate_random_pswd {
    # The sed character replacement makes the base64-string URL safe; for example required by lodgeit
    echo `dd if=/dev/urandom bs=1 count=$1 2>/dev/null | base64 -w $1 | head -n1 | sed -e 's#/#_#g;s#\+#_#g'`
}

function generate_api_key {
    out=""
    while [ ${#out} -lt 40 ]; do
            out=$out`echo "obase=16; $RANDOM" | bc`
    done

    out=${out:0:40}
    echo $out | awk '{print tolower($0)}'
}

function generate_hieras {
    OUTPUT=${BUILD}/hiera
    mkdir -p ${OUTPUT}

    cp puppet/hiera/* ${OUTPUT}/

    sed -i -e "s/SF_SUFFIX/${SF_SUFFIX}/g" ${OUTPUT}/common.yaml

    # MySQL password for services
    MYSQL_ROOT_SECRET=$(generate_random_pswd 8)
    REDMINE_MYSQL_SECRET=$(generate_random_pswd 8)
    GERRIT_MYSQL_SECRET=$(generate_random_pswd 8)
    ETHERPAD_MYSQL_SECRET=$(generate_random_pswd 8)
    LODGEIT_MYSQL_SECRET=$(generate_random_pswd 8)
    sed -i "s#MYSQL_ROOT_PWD#${MYSQL_ROOT_SECRET}#" ${OUTPUT}/mysql.yaml
    sed -i "s#REDMINE_SQL_PWD#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml
    sed -i "s#GERRIT_SQL_PWD#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml
    sed -i "s#ETHERPAD_SQL_PWD#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml
    sed -i "s#LODGEIT_SQL_PWD#${LODGEIT_MYSQL_SECRET}#" ${OUTPUT}/mysql.yaml

    # Default authorized ssh keys on each node
    JENKINS_PUB="$(cat ${OUTPUT}/../data/jenkins_rsa.pub | cut -d' ' -f2)"
    sed -i "s#JENKINS_PUB_KEY#${JENKINS_PUB}#" ${OUTPUT}/ssh_*.yaml
    SERVICE_PUB="$(cat ${OUTPUT}/../data/service_rsa.pub | cut -d' ' -f2)"
    sed -i "s#SERVICE_PUB_KEY#${SERVICE_PUB}#" ${OUTPUT}/ssh.yaml

    # Jenkins part
    JENKINS_DEFAULT_SLAVE="slave.${SF_SUFFIX}"
    JENKINS_USER_PASSWORD="${JUP}"
    sed -i "s#JENKINS_DEFAULT_SLAVE#${JENKINS_DEFAULT_SLAVE}#" ${OUTPUT}/jenkins.yaml
    sed -i "s#JENKINS_USER_PASSWORD#${JENKINS_USER_PASSWORD}#" ${OUTPUT}/jenkins.yaml

    # Redmine part
    REDMINE_API_KEY=$(generate_api_key)
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/redmine.yaml
    sed -i "s#REDMINE_MYSQL_SECRET#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/redmine.yaml

    # Gerrit part
    GERRIT_SERV_PUB="$(cat ${OUTPUT}/../data/gerrit_service_rsa.pub | cut -d' ' -f2)"
    GERRIT_ADMIN_PUB_KEY="$(cat ${OUTPUT}/../data/gerrit_admin_rsa.pub | cut -d' ' -f2)"
    GERRIT_EMAIL_PK=$(generate_random_pswd 32)
    GERRIT_TOKEN_PK=$(generate_random_pswd 32)
    sed -i "s#GERRIT_SERV_PUB_KEY#ssh-rsa ${GERRIT_SERV_PUB}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_SERV_KEY#${GERRIT_SERV_PUB}#" ${OUTPUT}/gerrit.yaml
    # Gerrit Jenkins pub key
    sed -i "s#JENKINS_PUB_KEY#ssh-rsa ${JENKINS_PUB}#" ${OUTPUT}/gerrit.yaml
    # Gerrit Admin pubkey
    sed -i "s#GERRIT_ADMIN_PUB_KEY#ssh-rsa ${GERRIT_ADMIN_PUB_KEY}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_KEY#${GERRIT_ADMIN_PUB_KEY}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_MYSQL_SECRET#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_EMAIL_PK#${GERRIT_EMAIL_PK}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_TOKEN_PK#${GERRIT_TOKEN_PK}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/gerrit.yaml

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
    local role=$1.${SF_SUFFIX}
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
    sed -i -e "s/SF_SUFFIX/${SF_SUFFIX}/g" ${OUTPUT}/hosts.yaml
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
    cp /root/sfconfig.yaml /etc/puppet/hiera/sf
    mkdir -p /etc/puppet/environments/sf/modules/ssh_keys/files/
    cp $DATA/service_rsa /etc/puppet/environments/sf/modules/ssh_keys/files/
    cp $DATA/jenkins_rsa /etc/puppet/environments/sf/modules/jenkins/files/
    cp $DATA/jenkins_rsa /etc/puppet/environments/sf/modules/zuul/files/
    cp $DATA/gerrit_admin_rsa /etc/puppet/environments/sf/modules/jenkins/files/
    cp $DATA/gerrit_service_rsa /etc/puppet/environments/sf/modules/gerrit/files/
    cp $DATA/gerrit_service_rsa.pub /etc/puppet/environments/sf/modules/gerrit/files/
    cp $DATA/gerrit_admin_rsa /etc/puppet/environments/sf/modules/managesf/files/
    cp $DATA/service_rsa /etc/puppet/environments/sf/modules/managesf/files/
    cp $DATA/gerrit_admin_rsa /etc/puppet/environments/sf/modules/jjb/files/
    chown -R puppet:puppet /etc/puppet/environments/sf
    chown -R puppet:puppet /etc/puppet/hiera/sf
    chown -R puppet:puppet /var/lib/puppet

    # generating keys for cauth
    keys_dir='/etc/puppet/environments/sf/modules/cauth/files/'
    mkdir -p $keys_dir
    openssl genrsa -out $keys_dir/privkey.pem 1024
    openssl rsa -in $keys_dir/privkey.pem -out $keys_dir/pubkey.pem -pubout
}

function run_puppet_agent {
    # Puppet agent will return code 2 on success...
    # We create a sub-process () and convert the error
    puppet agent --test --environment sf || (
        [ "$?" == 2 ] && exit 0
        echo "========================================="
        echo "FAIL: Puppet agent failed on puppetmaster"
        echo "========================================="
        exit 1
    )
    service puppet start
}

function run_puppet_agent_stop {
    # Be sure puppet agent is stopped
    local ssh_port=22
    for role in ${PUPPETIZED_ROLES}; do
        sshpass -p $TEMP_SSH_PWD ssh -p$ssh_port root@${role}.${SF_SUFFIX} "service puppet stop"
    done
}

function trigger_puppet_apply {
    local puppetmaster_ip=$(getip_from_yaml puppetmaster)
    local ssh_port=22
    for role in ${PUPPETIZED_ROLES}; do
        echo " [+] ${role}"
        sshpass -p $TEMP_SSH_PWD ssh -p$ssh_port root@${role}.${SF_SUFFIX} sed -i "s/puppetmaster-ip-template/$puppetmaster_ip/" /etc/hosts
        sshpass -p $TEMP_SSH_PWD scp $HOME/.ssh/known_hosts root@${role}.${SF_SUFFIX}:/root/.ssh/
        # The Puppet run will deactivate the temporary root password
        # Puppet agent will return code 2 on success...
        # We create a sub-process () and convert the error
        sshpass -p $TEMP_SSH_PWD ssh -p$ssh_port root@${role}.${SF_SUFFIX} "puppet agent --test --environment sf" || (
            [ "$?" == 2 ] && exit 0
            echo "======================================"
            echo "FAIL: Puppet agent failed for ${role}"
            echo "======================================"
            exit 1
        )
        # Run another time. Should take only a few seconds per node if nothing needs to be changed
        #ssh -p$ssh_port root@${role}.${SF_SUFFIX} "puppet agent --test --environment sf || true"
    done
}

function run_puppet_agent_start {
    # Start puppet agent at the end of the bootstrap
    local ssh_port=22
    for role in ${PUPPETIZED_ROLES}; do
        ssh -p$ssh_port root@${role}.${SF_SUFFIX} "sleep 2700; service puppet start" &
    done
}
