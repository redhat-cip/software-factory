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

# -----------------
# Functions
# -----------------
[ -z "${DEBUG}" ] || set -x

# Defaults
DOMAIN=$(cat /etc/puppet/hiera/sf/sfconfig.yaml | grep "^fqdn:" | cut -d: -f2 | sed 's/ //g')
BUILD=/root/sf-bootstrap-data
HOME=/root

export PATH=/bin:/sbin:/usr/local/bin:/usr/local/sbin

function update_config {
    echo "sf_version: $(grep ^VERS= /var/lib/edeploy/conf | cut -d"=" -f2 | cut -d'-' -f2)" > /etc/puppet/hiera/sf/sf_version.yaml
    /usr/local/bin/sf-update-hiera-config.py
    /usr/local/bin/sf-ansible-generate-inventory.py --domain ${DOMAIN} --install_server_ip $(ip route get 8.8.8.8 | awk '{ print $7 }') \
        /etc/puppet/hiera/sf/arch.yaml

    # set managesf gitconfig
    git config --global user.name "SF initial configurator"
    git config --global user.email admin@$DOMAIN
    git config --global gitreview.username "admin"
    git config --global push.default simple

    # update .ssh/config
    cat << EOF > /root/.ssh/config
Host ${DOMAIN}
    User admin
    Port 29418
    IdentityFile /root/sf-bootstrap-data/ssh_keys/gerrit_admin_rsa
EOF

    # Make sure the keys in bootstrap are same as in sfcreds.yaml. This is only
    # needed to run functional test because tests use this directory. A running
    # SF only uses data from /etc/puppet/hiera/sf/sfcreds.yaml.
    recreate_bootstrap_data
}

function generate_random_pswd {
    # The sed character replacement makes the base64-string URL safe; for example required by lodgeit
    echo `base64 -w $1 < /dev/urandom | head -n1 | sed -e 's#/#_#g;s#\+#_#g'`
}

function generate_api_key {
    out=""
    while [ ${#out} -lt 40 ]; do
            out=$out`echo "obase=16; $RANDOM" | bc`
    done

    out=${out:0:40}
    echo $out | awk '{print tolower($0)}'
}

function generate_yaml {
    OUTPUT=/etc/puppet/hiera/sf/
    echo "[sfconfig] copy defaults hiera to ${OUTPUT}"
    # MySQL password for services + service user
    MYSQL_ROOT_SECRET=$(generate_random_pswd 32)
    REDMINE_MYSQL_SECRET=$(generate_random_pswd 32)
    GERRIT_MYSQL_SECRET=$(generate_random_pswd 32)
    NODEPOOL_MYSQL_SECRET=$(generate_random_pswd 32)
    ETHERPAD_MYSQL_SECRET=$(generate_random_pswd 32)
    LODGEIT_MYSQL_SECRET=$(generate_random_pswd 32)
    GRAFANA_MYSQL_SECRET=$(generate_random_pswd 32)
    GNOCCHI_MYSQL_SECRET=$(generate_random_pswd 32)
    STORYBOARD_MYSQL_SECRET=$(generate_random_pswd 32)
    STORYBOARD_TOKEN_SECRET=$(generate_random_pswd 32)
    CAUTH_MYSQL_SECRET=$(generate_random_pswd 32)
    MANAGESF_MYSQL_SECRET=$(generate_random_pswd 32)
    SF_SERVICE_USER_SECRET=$(generate_random_pswd 32)
    MUMBLE_ICE_SECRET=$(generate_random_pswd 32)
    sed -i "s#MYSQL_ROOT_PWD#${MYSQL_ROOT_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#REDMINE_SQL_PWD#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GERRIT_SQL_PWD#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#NODEPOOL_SQL_PWD#${NODEPOOL_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#ETHERPAD_SQL_PWD#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#LODGEIT_SQL_PWD#${LODGEIT_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GRAFANA_SQL_PWD#${GRAFANA_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GNOCCHI_SQL_PWD#${GNOCCHI_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#STORYBOARD_SQL_PWD#${STORYBOARD_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#STORYBOARD_SERVICE_TOKEN#${STORYBOARD_TOKEN_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#CAUTH_SQL_PWD#${CAUTH_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#MANAGESF_SQL_PWD#${MANAGESF_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#SF_SERVICE_USER_PWD#${SF_SERVICE_USER_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#MUMBLE_ICE_SECRET#${MUMBLE_ICE_SECRET}#" ${OUTPUT}/sfcreds.yaml
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
    ETHERPAD_ADMIN_KEY=$(generate_random_pswd 32)
    sed -i "s#ETHERPAD_ADMIN_KEY#${ETHERPAD_ADMIN_KEY}#" ${OUTPUT}/sfcreds.yaml
    # Lodgeit/Paste part
    LODGEIT_SESSION_KEY=$(generate_random_pswd 32)
    sed -i "s#LODGEIT_SESSION_KEY#${LODGEIT_SESSION_KEY}#" ${OUTPUT}/sfcreds.yaml

    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/service_rsa service_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/jenkins_rsa jenkins_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/jenkins_rsa.pub jenkins_rsa_pub
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/gerrit_admin_rsa gerrit_admin_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/gerrit_service_rsa gerrit_service_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/gerrit_service_rsa.pub gerrit_service_rsa_pub
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/certs/privkey.pem privkey_pem
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/certs/pubkey.pem  pubkey_pem

    chown -R root:puppet /etc/puppet/hiera/sf
    chmod -R 0750 /etc/puppet/hiera/sf
}

function generate_keys {
    # Re-entrant method, need to check if file exists first before creating
    OUTPUT=${BUILD}/ssh_keys

    # Service key is used to allow root access from managesf to other nodes
    [ -f ${OUTPUT}/service_rsa ]        || ssh-keygen -N '' -f ${OUTPUT}/service_rsa > /dev/null
    [ -f ${OUTPUT}/jenkins_rsa ]        || ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa > /dev/null
    [ -f ${OUTPUT}/gerrit_service_rsa ] || ssh-keygen -N '' -f ${OUTPUT}/gerrit_service_rsa > /dev/null
    [ -f ${OUTPUT}/gerrit_admin_rsa ]   || ssh-keygen -N '' -f ${OUTPUT}/gerrit_admin_rsa > /dev/null

    # generating keys for cauth
    OUTPUT=${BUILD}/certs
    [ -f ${OUTPUT}/privkey.pem ]        || openssl genrsa -out ${OUTPUT}/privkey.pem 1024
    [ -f ${OUTPUT}/pubkey.pem ]         || openssl rsa -in ${OUTPUT}/privkey.pem -out ${OUTPUT}/pubkey.pem -pubout

    [ -d "${HOME}/.ssh" ] || mkdir -m 0700 "${HOME}/.ssh"
    [ -f "${HOME}/.ssh/known_hosts" ] || touch "${HOME}/.ssh/known_hosts"

    # SSL certificate
    OUTPUT=${BUILD}/certs
    # Generate self-signed Apache certificate
    [ -f openssl.cnf ] || cat > openssl.cnf << EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[ req_distinguished_name ]
commonName_default = ${DOMAIN}

[ v3_req ]
subjectAltName=@alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = auth.${DOMAIN}
EOF
    [ -f ${OUTPUT}/gateway.key ] || {
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 -subj "/C=FR/O=SoftwareFactory/CN=${DOMAIN}" \
            -keyout ${OUTPUT}/gateway.key -out ${OUTPUT}/gateway.crt -extensions v3_req -config openssl.cnf
        hieraedit.py --yaml /etc/puppet/hiera/sf/sfcreds.yaml -f ${OUTPUT}/gateway.key gateway_key
        hieraedit.py --yaml /etc/puppet/hiera/sf/sfcreds.yaml -f ${OUTPUT}/gateway.crt gateway_crt
        hieraedit.py --yaml /etc/puppet/hiera/sf/sfcreds.yaml -f ${OUTPUT}/gateway.crt gateway_chain
        # Trust this certificate. This is mostly required for sfmanager
        cat ${OUTPUT}/gateway.crt >> /etc/pki/tls/certs/ca-bundle.crt
    }
    # Update missing chain configuration (TODO: move this to global config updater (coming soon))
    grep -q '^gateway_chain:' /etc/puppet/hiera/sf/sfcreds.yaml || \
        hieraedit.py --yaml /etc/puppet/hiera/sf/sfcreds.yaml -f ${OUTPUT}/gateway.crt gateway_chain
}

function recreate_bootstrap_data {
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('service_rsa')" > ${BUILD}/ssh_keys/service_rsa
    echo -n "ssh-rsa " > ${BUILD}/ssh_keys/service_rsa.pub
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('creds_service_pub_key')" >> ${BUILD}/ssh_keys/service_rsa.pub
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('jenkins_rsa')" > ${BUILD}/ssh_keys/jenkins_rsa
    echo -n "ssh-rsa " > ${BUILD}/ssh_keys/jenkins_rsa.pub
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('jenkins_rsa_pub')" >> ${BUILD}/ssh_keys/jenkins_rsa.pub
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('gerrit_admin_rsa')" > ${BUILD}/ssh_keys/gerrit_admin_rsa
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('gerrit_service_rsa')" > ${BUILD}/ssh_keys/gerrit_service_rsa
    echo -n "ssh-rsa " > ${BUILD}/ssh_keys/gerrit_service_rsa.pub
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('gerrit_service_rsa_pub')" >> ${BUILD}/ssh_keys/gerrit_service_rsa.pub
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('privkey_pem')" > ${BUILD}/certs/privkey_pem
    python -c "import yaml;print yaml.load(open('/etc/puppet/hiera/sf/sfcreds.yaml')).get('pubkey_pem')" > ${BUILD}/certs/pubkey_pem
}


function wait_for_ssh {
    local host=$1
    while true; do
        KEY=$(ssh-keyscan -p 22 $host 2> /dev/null | grep ssh-rsa)
        if [ "$KEY" != ""  ]; then
            grep -q ${host} ${HOME}/.ssh/known_hosts || (echo $KEY >> $HOME/.ssh/known_hosts)
            echo "  -> $host:22 is up!"
            return 0
        fi
        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && return 1
        echo "  [E] ssh-keyscan on $host_ip:22 failed, will retry in 1 seconds (attempt $RETRIES/40)"
        sleep 1
    done
}


# -----------------
# End of functions
# -----------------

# Generate site specifics configuration
# Make sure sf-bootstrap-data sub-directories exist
for i in hiera ssh_keys certs; do
    [ -d ${BUILD}/$i ] || mkdir -p ${BUILD}/$i
done
generate_keys
if [ ! -f "${BUILD}/generate.done" ]; then
    generate_yaml
    touch "${BUILD}/generate.done"
fi

if [ -f "/etc/puppet/hiera/sf/sfcreds.yaml.orig" ]; then
    # Most likely this is a sfconfig.sh run after restoring a backup.
    # We need to update the mysql root password
    oldpw=`grep -Po "(?<=creds_mysql_root_pwd: ).*" /etc/puppet/hiera/sf/sfcreds.yaml.orig`
    newpw=`grep -Po "(?<=creds_mysql_root_pwd: ).*" /etc/puppet/hiera/sf/sfcreds.yaml`
    mysqladmin -u root -p"$oldpw" password "$newpw" && rm /etc/puppet/hiera/sf/sfcreds.yaml.orig
fi

update_config

# Configure ssh access to inventory and copy puppet configuration
HOSTS=$(awk "/${DOMAIN}/ { print \$1 }" /etc/ansible/hosts | sort | uniq)
for host in $HOSTS; do
    wait_for_ssh $host
done

echo "[sfconfig] Starting configuration"
time ansible-playbook /etc/ansible/sf_main.yml || {
    echo "[sfconfig] sfpuppet playbook failed"
    exit 1
}

time ansible-playbook /etc/ansible/sf_initialize.yml || {
    echo "[sfconfig] sfmain playbook failed"
    exit 1
}

echo "${DOMAIN}: SUCCESS"
exit 0
