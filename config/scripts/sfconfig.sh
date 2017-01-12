#!/bin/bash
#
# copyright (c) 2014 enovance sas <licensing@enovance.com>
# copyright (c) 2016 Red Hat
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
set -e

logger "sfconfig.sh: started"
echo "[$(date)] Running sfconfig.sh"

# Defaults
DOMAIN=$(cat /etc/software-factory/sfconfig.yaml | grep "^fqdn:" | cut -d: -f2 | sed 's/ //g')
HOME=/root

export PATH=/bin:/sbin:/usr/local/bin:/usr/local/sbin

function wait_for_ssh {
    [ -d "${HOME}/.ssh" ] || mkdir -m 0700 "${HOME}/.ssh"
    [ -f "${HOME}/.ssh/known_hosts" ] || touch "${HOME}/.ssh/known_hosts"

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

/usr/local/bin/sf-update-hiera-config.py
/usr/local/bin/sf-ansible-generate-inventory.py                         \
    --domain ${DOMAIN}                                                  \
    --install_server_ip $(ip route get 8.8.8.8 | awk '{ print $7 }')    \
    /etc/software-factory/arch.yaml
/usr/local/bin/sfconfig.py


# Configure ssh access to inventory
HOSTS=$(awk "/${DOMAIN}/ { print \$1 }" /etc/ansible/hosts | sort | uniq)
for host in $HOSTS; do
    wait_for_ssh $host
done

time ansible-playbook /etc/ansible/sf_setup.yml || {
    echo "[sfconfig] sf_setup playbook failed"
    exit 1
}

time ansible-playbook /etc/ansible/sf_initialize.yml || {
    echo "[sfconfig] sf_initialize playbook failed"
    exit 1
}

time ansible-playbook /etc/ansible/sf_postconf.yml || {
    echo "[sfconfig] sf_postconf playbook failed"
    exit 1
}

logger "sfconfig.sh: ended"
echo "${DOMAIN}: SUCCESS"
echo
echo "Access dashboard: https://${DOMAIN}"
echo "Login with admin user, get the admin password by running:"
echo "  awk '/admin_password/ {print \$2}' /etc/software-factory/sfconfig.yaml"
exit 0
