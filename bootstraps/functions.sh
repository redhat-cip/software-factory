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

BUILD=${BUILD:-/root/sf-bootstrap-data}

function generate_hosts_yaml {
    OUTPUT=${BUILD}/hiera
    cat << EOF > ${OUTPUT}/hosts.yaml
hosts:
  localhost:
    ip: 127.0.0.1
  puppetmaster.SF_SUFFIX:
    ip: 192.168.135.54
    host_aliases: [puppetmaster]
  mysql.SF_SUFFIX:
    ip: 192.168.135.54
    host_aliases: [mysql]
  jenkins.SF_SUFFIX:
    ip: 192.168.135.54
    host_aliases: [jenkins]
  redmine.SF_SUFFIX:
    ip: 192.168.135.54
    host_aliases: [redmine]
  api-redmine.SF_SUFFIX:
    ip: 192.168.135.54
  gerrit.SF_SUFFIX:
    ip: 192.168.135.54
    host_aliases: [gerrit]
  managesf.SF_SUFFIX:
    ip: 192.168.135.54
    host_aliases: [managesf, auth.SF_SUFFIX, SF_SUFFIX]
EOF
    sed -i "s/SF_SUFFIX/${SF_SUFFIX}/g" ${OUTPUT}/hosts.yaml
}

function generate_sfconfig {
    OUTPUT=${BUILD}/hiera
    cp sfconfig.yaml ${OUTPUT}/
    # Set and generated admin password
    DEFAULT_ADMIN_USER=$(cat ${OUTPUT}/sfconfig.yaml | grep '^admin_name:' | awk '{ print $2 }')
    DEFAULT_ADMIN_PASSWORD=$(cat ${OUTPUT}/sfconfig.yaml | grep '^admin_password:' | awk '{ print $2 }')
    ADMIN_USER=${ADMIN_USER:-${DEFAULT_ADMIN_USER}}
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-${DEFAULT_ADMIN_PASSWORD}}
    sed -i "s/^admin_name:.*/admin_name: ${ADMIN_USER}/" ${OUTPUT}/sfconfig.yaml
    # TODO: remove this, it should work without
    sed -i "s/^admin_password:.*/admin_password: ${ADMIN_PASSWORD}/" ${OUTPUT}/sfconfig.yaml
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
    MYSQL_ROOT_SECRET=$(generate_random_pswd 32)
    REDMINE_MYSQL_SECRET=$(generate_random_pswd 32)
    GERRIT_MYSQL_SECRET=$(generate_random_pswd 32)
    NODEPOOL_MYSQL_SECRET=$(generate_random_pswd 32)
    ETHERPAD_MYSQL_SECRET=$(generate_random_pswd 32)
    LODGEIT_MYSQL_SECRET=$(generate_random_pswd 32)
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
    JENKINS_USER_PASSWORD="$(generate_random_pswd 32)"
    sed -i "s#JENKINS_USER_PASSWORD#${JENKINS_USER_PASSWORD}#" ${OUTPUT}/sfcreds.yaml
    # Etherpad part
    ETHERPAD_SESSION_KEY=$(generate_random_pswd 32)
    sed -i "s#ETHERPAD_SESSION_KEY#${ETHERPAD_SESSION_KEY}#" ${OUTPUT}/sfcreds.yaml
    # Lodgeit/Paste part
    LODGEIT_SESSION_KEY=$(generate_random_pswd 32)
    sed -i "s#LODGEIT_SESSION_KEY#${LODGEIT_SESSION_KEY}#" ${OUTPUT}/sfcreds.yaml
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
    cp ${HIERA}/hosts.yaml /etc/puppet/hiera/sf
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
