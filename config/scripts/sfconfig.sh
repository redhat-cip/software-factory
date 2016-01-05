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
[ -z "${DEBUG}" ] && DISABLE_SETX=1 || set -x

# Defaults
DOMAIN=$(cat /etc/puppet/hiera/sf/sfconfig.yaml | grep "^fqdn:" | cut -d: -f2 | sed 's/ //g')
REFARCH=1node-allinone
BUILD=/root/sf-bootstrap-data
HOME=/root


function update_sfconfig {
    OUTPUT=${BUILD}/hiera
    # get public ip of managesf
    local localip=$(ip route get 8.8.8.8 | awk '{ print $7 }')
    local localalias="${DOMAIN}, mysql.${DOMAIN}, mysql, redmine.${DOMAIN}, redmine, api-redmine.${DOMAIN}, api-redmine, gerrit.${DOMAIN}, gerrit, managesf, auth.${DOMAIN}, auth, statsd.${DOMAIN}, statsd"
    if [ -n "${IP_JENKINS}" ]; then
        local jenkins_host="  jenkins.${DOMAIN}:      {ip: ${IP_JENKINS}, host_aliases: [jenkins, nodepool.${DOMAIN}]}"
    else
        localalias="${localalias}, jenkins.${DOMAIN}, jenkins, nodepool.${DOMAIN}"
    fi
    cat << EOF > ${OUTPUT}/hosts.yaml
hosts:
  localhost:              {ip: 127.0.0.1}
  managesf.${DOMAIN}:     {ip: ${localip}, host_aliases: [$localalias]}
EOF
    [ -n "${jenkins_host}" ] && echo "${jenkins_host}" >> ${OUTPUT}/hosts.yaml
    hieraedit.py --yaml ${OUTPUT}/sfconfig.yaml fqdn       "${DOMAIN}"
    hieraedit.py --yaml ${OUTPUT}/sfarch.yaml   refarch    "${REFARCH}"
    hieraedit.py --yaml ${OUTPUT}/sfarch.yaml   ip_jenkins "${IP_JENKINS}"
    echo "sf_version: $(grep ^VERS= /var/lib/edeploy/conf | cut -d"=" -f2 | cut -d'-' -f2)" > /etc/puppet/hiera/sf/sf_version.yaml

    # update inventory
    cat << EOF > /etc/ansible/hosts
[managesf]
managesf.${DOMAIN}

[jenkins]
jenkins.${DOMAIN}
EOF
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

function generate_yaml {
    OUTPUT=${BUILD}/hiera
    echo "[sfconfig] copy defaults hiera to ${OUTPUT}"
    mv /etc/puppet/hiera/sf/sfconfig.yaml ${OUTPUT}/ || exit -1
    mv /etc/puppet/hiera/sf/sfcreds.yaml ${OUTPUT}/
    mv /etc/puppet/hiera/sf/sfarch.yaml ${OUTPUT}/
    # MySQL password for services + service user
    MYSQL_ROOT_SECRET=$(generate_random_pswd 32)
    REDMINE_MYSQL_SECRET=$(generate_random_pswd 32)
    GERRIT_MYSQL_SECRET=$(generate_random_pswd 32)
    NODEPOOL_MYSQL_SECRET=$(generate_random_pswd 32)
    ETHERPAD_MYSQL_SECRET=$(generate_random_pswd 32)
    LODGEIT_MYSQL_SECRET=$(generate_random_pswd 32)
    GRAPHITE_MYSQL_SECRET=$(generate_random_pswd 32)
    GRAPHITE_SECRET_KEY=$(generate_random_pswd 32)
    GRAFANA_MYSQL_SECRET=$(generate_random_pswd 32)
    SF_SERVICE_USER_SECRET=$(generate_random_pswd 32)
    sed -i "s#MYSQL_ROOT_PWD#${MYSQL_ROOT_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#REDMINE_SQL_PWD#${REDMINE_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GERRIT_SQL_PWD#${GERRIT_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#NODEPOOL_SQL_PWD#${NODEPOOL_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#ETHERPAD_SQL_PWD#${ETHERPAD_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#LODGEIT_SQL_PWD#${LODGEIT_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GRAPHITE_SQL_PWD#${GRAPHITE_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GRAPHITE_SECRET_KEY#${GRAPHITE_SECRET_KEY}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#GRAFANA_SQL_PWD#${GRAFANA_MYSQL_SECRET}#" ${OUTPUT}/sfcreds.yaml
    sed -i "s#SF_SERVICE_USER_PWD#${SF_SERVICE_USER_SECRET}#" ${OUTPUT}/sfcreds.yaml
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

    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/service_rsa service_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/jenkins_rsa jenkins_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/jenkins_rsa.pub jenkins_rsa_pub
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/gerrit_admin_rsa gerrit_admin_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/gerrit_service_rsa gerrit_service_rsa
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/ssh_keys/gerrit_service_rsa.pub gerrit_service_rsa_pub
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/certs/privkey.pem privkey_pem
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/certs/pubkey.pem  pubkey_pem
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/certs/gateway.key gateway_key
    hieraedit.py --yaml ${OUTPUT}/sfcreds.yaml -f ${BUILD}/certs/gateway.crt gateway_crt

    ln -sf ${OUTPUT}/sfconfig.yaml /etc/puppet/hiera/sf/sfconfig.yaml
    ln -sf ${OUTPUT}/sfcreds.yaml /etc/puppet/hiera/sf/sfcreds.yaml
    ln -sf ${OUTPUT}/hosts.yaml /etc/puppet/hiera/sf/hosts.yaml

    chown -R root:puppet /etc/puppet/hiera/sf
    chmod -R 0750 /etc/puppet/hiera/sf
}

function generate_keys {
    OUTPUT=${BUILD}/ssh_keys

    # Service key is used to allow root access from managesf to other nodes
    ssh-keygen -N '' -f ${OUTPUT}/service_rsa > /dev/null
    ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa > /dev/null
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_service_rsa > /dev/null
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_admin_rsa > /dev/null
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
commonName_default = ${DOMAIN}

[ v3_req ]
subjectAltName=@alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = auth.${DOMAIN}
EOF
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -subj "/C=FR/O=SoftwareFactory/CN=${DOMAIN}" -keyout ${OUTPUT}/gateway.key -out ${OUTPUT}/gateway.crt -extensions v3_req -config openssl.cnf
}

function wait_for_ssh {
    local ip=$1
    echo "[sfconfig][$ip] Waiting for ssh..."
    [ -d "${HOME}/.ssh" ] || mkdir -m 0700 "${HOME}/.ssh"
    while true; do
        KEY=`ssh-keyscan -p 22 $ip`
        if [ "$KEY" != ""  ]; then
            ssh-keyscan $ip | grep ssh-rsa | tee -a "$HOME/.ssh/known_hosts"
            echo "  -> $ip:22 is up!"
            return 0
        fi
        let RETRIES=RETRIES+1
        [ "$RETRIES" == "40" ] && return 1
        echo "  [E] ssh-keyscan on $ip:22 failed, will retry in 1 seconds (attempt $RETRIES/40)"
        sleep 1
    done
}

function puppet_apply_host {
    echo "[sfconfig] Applying hosts.pp"
    # Set /etc/hosts to a known state...
    grep -q localdomain /etc/hosts && echo "127.0.0.1       localhost" > /etc/hosts
    # Update local /etc/hosts
    puppet apply --test --environment sf --modulepath=/etc/puppet/environments/sf/modules/:/etc/puppet/modules/ -e "include hosts"
}

function puppet_apply {
    host=$1
    manifest=$2
    echo "[sfconfig][$host] Applying $manifest" | tee -a /var/log/puppet_apply.log
    [ "$host" == "managesf.${DOMAIN}" ] && ssh="" || ssh="ssh -tt root@$host"
    $ssh puppet apply --test --environment sf --modulepath=/etc/puppet/environments/sf/modules/:/etc/puppet/modules/ $manifest 2>&1 \
        | tee -a /var/log/puppet_apply.log | grep '\(Info:\|Warning:\|Error:\|Notice: Compiled\|Notice: Finished\)'
    res=$?
    if [ "$res" != 2 ] && [ "$res" != 0 ]; then
        echo "[sfconfig][$host] Failed ($res) to apply $manifest"
        exit 1
    fi
}

function puppet_copy {
    host=$1
    echo "[sfconfig][$host] Copy puppet configuration"
    rsync -a -L --delete /etc/puppet/hiera/ ${host}:/etc/puppet/hiera/
}

# -----------------
# End of functions
# -----------------

while getopts ":a:i:h" opt; do
    case $opt in
        a)
            REFARCH=$OPTARG
            [ $REFARCH != "1node-allinone" -a $REFARCH != "2nodes-jenkins" ] && {
                    echo "Available REFARCH are: 1node-allinone or 2nodes-jenkins"
                    exit 1
            }
            ;;
        i)
            IP_JENKINS=$OPTARG
            ;;
        h)
            echo ""
            echo "Usage:"
            echo ""
            echo "If run without any options sfconfig script will use defaults:"
            echo "REFARCH=1node-allinone"
            echo ""
            echo "Use the -a option to specify the REFARCH."
            echo ""
            echo "If REFARCH is 2nodes-jenkins then is is expected you pass"
            echo "the ip of the node where the CI system will be installed"
            echo "via the -i option."
            echo ""
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
done

# Make sure hostname is correct
if [ "$(hostname -f)" != "managesf.${DOMAIN}" ]; then
    echo "[sfconfig][$(hostname -f)] Changing hostname to managesf.${DOMAIN}"
    hostnamectl set-hostname "managesf.${DOMAIN}"
fi

# Generate site specifics configuration
if [ ! -f "${BUILD}/generate.done" ]; then
    # Make sure sf-bootstrap-data sub-directories exist
    for i in hiera ssh_keys certs; do
        [ -d ${BUILD}/$i ] || mkdir -p ${BUILD}/$i
    done
    generate_keys
    generate_apache_cert
    generate_yaml
    touch "${BUILD}/generate.done"
else
    # During upgrade or another sfconfig run, reuse the same refarch and jenkins ip
    REFARCH=$(cat ${BUILD}/hiera/sfarch.yaml | sed 's/ //g' | grep "^refarch:" | cut -d: -f2)
    IP_JENKINS=$(cat ${BUILD}/hiera/sfarch.yaml | sed 's/ //g' | grep "^jenkins_ip:" | cut -d: -f2)
fi

update_sfconfig
puppet_apply_host
wait_for_ssh "managesf.${DOMAIN}"
wait_for_ssh "jenkins.${DOMAIN}"
echo "[sfconfig] Boostrapping $REFARCH"
# Apply puppet stuff with good old shell scrips
case "${REFARCH}" in
    "1node-allinone")
        puppet_apply "managesf.${DOMAIN}" /etc/puppet/environments/sf/manifests/1node-allinone.pp
        ;;
    "2nodes-jenkins")
        [ "$IP_JENKINS" == "127.0.0.1" ] && {
            echo "[sfconfig] Please select another IP_JENKINS than 127.0.0.1 for this REFARCH"
            exit 1
        }
        puppet_copy jenkins.${DOMAIN}

        # Run puppet apply
        puppet_apply "managesf.${DOMAIN}" /etc/puppet/environments/sf/manifests/2nodes-sf.pp
        puppet_apply "jenkins.${DOMAIN}" /etc/puppet/environments/sf/manifests/2nodes-jenkins.pp
        ;;
    *)
        echo "Unknown refarch ${REFARCH}"
        exit 1
        ;;
esac

echo "[sfconfig] Ansible configuration"
cd /usr/local/share/sf-ansible
[ -d group_vars ] || {
    mkdir group_vars
    ln -s /etc/puppet/hiera/sf/sfconfig.yaml group_vars/all.yaml
}
ansible-playbook sfmain.yaml || {
    echo "[sfconfig] Ansible playbook failed"
    exit 1
}

echo "SUCCESS ${REFARCH}"
exit 0
