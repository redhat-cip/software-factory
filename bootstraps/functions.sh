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

BUILD=${BUILD:-/root/sf-bootstrap-data}

INITIAL=${INITIAL:-yes}

if [ "$INITIAL" = "no" ]; then
    # Keys has been setup on the nodes
    SSHPASS=""
else
    SSHPASS="sshpass -p $TEMP_SSH_PWD"
fi

function hash_password {
    python -c "import crypt, random, string; salt = '\$6\$' + ''.join(random.choice(string.letters + string.digits) for _ in range(16)) + '\$'; print crypt.crypt('$1', salt)"
}

function generate_sfconfig {
    # Write sfconfig.yaml to $1
    SFCONFIGFILE=$1
    cp ../sfconfig.yaml $SFCONFIGFILE || return # quit if copy failed

    # Set and generated admin password
    DEFAULT_ADMIN_USER=$(cat $SFCONFIGFILE | grep '^admin_name:' | awk '{ print $2 }')
    DEFAULT_ADMIN_PASSWORD=$(cat $SFCONFIGFILE | grep '^admin_password:' | awk '{ print $2 }')
    ADMIN_USER=${ADMIN_USER:-${DEFAULT_ADMIN_USER}}
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-${DEFAULT_ADMIN_PASSWORD}}
    ADMIN_PASSWORD_HASHED=$(hash_password "${ADMIN_PASSWORD}")
    sed -i "s/^admin_name:.*/admin_name: ${ADMIN_USER}/" $SFCONFIGFILE

    # TODO: remove this, it should work without
    sed -i "s/^admin_password:.*/admin_password: ${ADMIN_PASSWORD}/" $SFCONFIGFILE

    # Make sure admin password is hashed and avoid duplicate entry
    grep -q "^admin_password_hashed:" $SFCONFIGFILE && {
        sed -i "s/^admin_password_hashed:.*/admin_password_hashed: \"${ADMIN_PASSWORD_HASHED}\"/" $SFCONFIGFILE
    } || {
        echo "admin_password_hashed: \"${ADMIN_PASSWORD_HASHED}\"" >> $SFCONFIGFILE
    }
}

function getip_from_yaml {
    cat /etc/puppet/hiera/sf/hosts.yaml  | grep -A 1 "^  $1" | grep 'ip:' | cut -d: -f2 | sed 's/ *//g'
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

function generate_creds_yaml {
    OUTPUT=${BUILD}/hiera
    cp sfcreds.yaml ${OUTPUT}/
    # MySQL password for services
    MYSQL_ROOT_SECRET=$(generate_random_pswd 8)
    REDMINE_MYSQL_SECRET=$(generate_random_pswd 8)
    GERRIT_MYSQL_SECRET=$(generate_random_pswd 8)
    NODEPOOL_MYSQL_SECRET=$(generate_random_pswd 8)
    ETHERPAD_MYSQL_SECRET=$(generate_random_pswd 8)
    LODGEIT_MYSQL_SECRET=$(generate_random_pswd 8)
    sed -i "s#MYSQL_ROOT_PWD#${MYSQL_ROOT_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#REDMINE_SQL_PWD#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GERRIT_SQL_PWD#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#NODEPOOL_SQL_PWD#${NODEPOOL_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#ETHERPAD_SQL_PWD#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#LODGEIT_SQL_PWD#${LODGEIT_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    # Default authorized ssh keys on each node
    JENKINS_PUB="$(cat ${BUILD}/ssh_keys/jenkins_rsa.pub | cut -d' ' -f2)"
    SERVICE_PUB="$(cat ${BUILD}/ssh_keys/service_rsa.pub | cut -d' ' -f2)"
    sed -i "s#JENKINS_PUB_KEY#${JENKINS_PUB}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#SERVICE_PUB_KEY#${SERVICE_PUB}#" ${OUTPUT}/sfcreds.yaml
    # Redmine part
    REDMINE_API_KEY=$(generate_api_key)
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/sfcreds.yaml
    # Gerrit part
    GERRIT_EMAIL_PK=$(generate_random_pswd 32)
    GERRIT_TOKEN_PK=$(generate_random_pswd 32)
    GERRIT_SERV_PUB="$(cat ${BUILD}/ssh_keys/gerrit_service_rsa.pub | cut -d' ' -f2)"
    GERRIT_ADMIN_PUB_KEY="$(cat ${BUILD}/ssh_keys/gerrit_admin_rsa.pub | cut -d' ' -f2)"
    sed -i "s#GERRIT_EMAIL_PK#${GERRIT_EMAIL_PK}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GERRIT_TOKEN_PK#${GERRIT_TOKEN_PK}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GERRIT_SERV_PUB_KEY#${GERRIT_SERV_PUB}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GERRIT_ADMIN_PUB_KEY#${GERRIT_ADMIN_PUB_KEY}#" ${OUTPUT}/sfcreds.yaml
    # Jenkins part
    JENKINS_USER_PASSWORD="${JUP}" # passed by cloudinit
    sed -i "s#JENKINS_USER_PASSWORD#${JENKINS_USER_PASSWORD}#" ${OUTPUT}/sfcreds.yaml
    # Etherpad part
    ETHERPAD_SESSION_KEY=$(generate_random_pswd 10)
    sed -i "s#ETHERPAD_SESSION_KEY#${ETHERPAD_SESSION_KEY}#" ${OUTPUT}/sfcreds.yaml
    # Lodgeit/Paste part
    LODGEIT_SESSION_KEY=$(generate_random_pswd 10)
    sed -i "s#LODGEIT_SESSION_KEY#${LODGEIT_SESSION_KEY}#" ${OUTPUT}/sfcreds.yaml
}

function wait_all_nodes {
    local port=22
    for role in $ROLES; do
        ip=$(getip_from_yaml $role)
        echo $role $ip
        scan_and_configure_knownhosts "$role" $ip $port
    done
    # Install ssh key on slave because it's not part of the puppet gang:
    if [ "$INITIAL" = "yes" ]; then
        $SSHPASS ssh-copy-id $(getip_from_yaml slave)
    fi
}

function scan_and_configure_knownhosts {
    local fqdn=$1.${SF_SUFFIX}
    local hostname=$1
    local ip=$2
    local port=$3
    if [ "$port" != "22" ]; then
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$fqdn]:$port" > /dev/null 2>&1 || echo
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$ip]:$port" > /dev/null 2>&1 || echo
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$hostname]:$port" > /dev/null 2>&1 || echo
    else
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$fqdn" > /dev/null 2>&1 || echo
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$ip" > /dev/null 2>&1 || echo
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$hostname" > /dev/null 2>&1 || echo
    fi
    RETRIES=0
    echo " [+] Starting ssh-keyscan on $fqdn:$port"
    while true; do
        KEY=`ssh-keyscan -p $port $fqdn 2> /dev/null`
        if [ "$KEY" != ""  ]; then
                # fix ssh-keyscan bug for 2 ssh server on different port
                if [ "$port" != "22" ]; then
                    ssh-keyscan -p $port $fqdn 2> /dev/null | sed "s/$fqdn/[$fqdn]:$port,[$ip]:$port,[$hostname]:$port/" >> "$HOME/.ssh/known_hosts"
                else
                    ssh-keyscan $fqdn 2> /dev/null | sed "s/$fqdn/$fqdn,$ip,$hostname/" >> "$HOME/.ssh/known_hosts"
                fi
                echo "  -> $fqdn:$port is up!"
                break
        fi

        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && break
        echo "  [E] ssh-keyscan on $fqdn:$port failed, will retry in 5 seconds (attempt $RETRIES/40)"
        sleep 10
    done
}

function generate_keys {
    OUTPUT=${BUILD}/ssh_keys
    # Service key is used to allow puppetmaster root to
    # connect on other node as root
    ssh-keygen -N '' -f ${OUTPUT}/service_rsa
    cp ${OUTPUT}/service_rsa /root/.ssh/id_rsa
    ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_service_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_admin_rsa
    # generating keys for cauth
    OUTPUT=${BUILD}/certs
    openssl genrsa -out ${OUTPUT}/privkey.pem 1024
    openssl rsa -in ${OUTPUT}/privkey.pem -out ${OUTPUT}/pubkey.pem -pubout
}

function generate_apache_cert {
    OUTPUT=${BUILD}/certs
    # Generate self-signed Apache certificate
    cat > openssl.cnf << EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[ req_distinguished_name ]
commonName_default = ${SF_SUFFIX}

[ v3_req ]
subjectAltName=@alt_names

[alt_names]
DNS.1 = ${SF_SUFFIX}
DNS.2 = auth.${SF_SUFFIX}
EOF
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -subj "/C=FR/O=SoftwareFactory/CN=${SF_SUFFIX}" -keyout ${OUTPUT}/gateway.key -out ${OUTPUT}/gateway.crt -extensions v3_req -config openssl.cnf
}

function prepare_etc_puppet {
    SSH_KEYS=${BUILD}/ssh_keys
    CERTS=${BUILD}/certs
    HIERA=${BUILD}/hiera
    cp ${HIERA}/sfconfig.yaml /etc/puppet/hiera/sf
    cp ${HIERA}/sfcreds.yaml /etc/puppet/hiera/sf
    TMP_VERSION=$(grep ^VERS= /var/lib/edeploy/conf | cut -d"=" -f2)
    if [ -z "${TMP_VERSION}" ]; then
        echo "FAIL: could not find edeploy version in /var/lib/edeploy/conf..."
        exit -1
    fi
    echo "sf_version: $(echo ${TMP_VERSION} | cut -d'-' -f2)" > /etc/puppet/hiera/sf/sf_version.yaml
    cp ${SSH_KEYS}/service_rsa /etc/puppet/environments/sf/modules/ssh_keys/files/
    cp ${SSH_KEYS}/service_rsa /root/.ssh/id_rsa
    cp ${SSH_KEYS}/service_rsa.pub /root/.ssh/id_rsa.pub
    cp ${SSH_KEYS}/jenkins_rsa /etc/puppet/environments/sf/modules/jenkins/files/
    cp ${SSH_KEYS}/jenkins_rsa /etc/puppet/environments/sf/modules/zuul/files/
    cp ${SSH_KEYS}/jenkins_rsa.pub /etc/puppet/environments/sf/modules/nodepool/files/
    cp ${SSH_KEYS}/gerrit_admin_rsa /etc/puppet/environments/sf/modules/jenkins/files/
    cp ${SSH_KEYS}/gerrit_service_rsa /etc/puppet/environments/sf/modules/gerrit/files/
    cp ${SSH_KEYS}/gerrit_service_rsa.pub /etc/puppet/environments/sf/modules/gerrit/files/
    cp ${SSH_KEYS}/gerrit_admin_rsa /etc/puppet/environments/sf/modules/managesf/files/
    cp ${SSH_KEYS}/service_rsa /etc/puppet/environments/sf/modules/managesf/files/
    cp ${SSH_KEYS}/gerrit_admin_rsa /etc/puppet/environments/sf/modules/jjb/files/
    cp ${CERTS}/privkey.pem /etc/puppet/environments/sf/modules/cauth/files/
    cp ${CERTS}/pubkey.pem /etc/puppet/environments/sf/modules/cauth/files/
    cp ${CERTS}/gateway.key /etc/puppet/environments/sf/modules/commonservices-apache/files/
    cp ${CERTS}/gateway.crt /etc/puppet/environments/sf/modules/commonservices-apache/files/
    cp ${CERTS}/gateway.crt /etc/puppet/environments/sf/modules/https_cert/files/
    chown -R puppet:puppet /etc/puppet/environments/sf
    chown -R puppet:puppet /etc/puppet/hiera/sf
    chown -R puppet:puppet /var/lib/puppet
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
        $SSHPASS ssh -p$ssh_port root@${role}.${SF_SUFFIX} "service puppet stop"
    done
}

function trigger_puppet_apply {
    local puppetmaster_ip=$(getip_from_yaml puppetmaster)
    local ssh_port=22
    for role in ${PUPPETIZED_ROLES}; do
        echo " [+] ${role}"
        $SSHPASS ssh -p$ssh_port root@${role}.${SF_SUFFIX} sed -i "s/puppetmaster-ip-template/$puppetmaster_ip/" /etc/hosts
        $SSHPASS scp $HOME/.ssh/known_hosts root@${role}.${SF_SUFFIX}:/root/.ssh/
        # The Puppet run will deactivate the temporary root password
        # Puppet agent will return code 2 on success...
        # We create a sub-process () and convert the error
        $SSHPASS ssh -p$ssh_port root@${role}.${SF_SUFFIX} "puppet agent --test --environment sf" || (
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
