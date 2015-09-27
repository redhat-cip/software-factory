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

DEBUG=1
source functions.sh

BUILD=/root/sf-bootstrap-data
REFARCH=${1:-1node-allinone}

# Make sure sf-bootstrap-data sub-directories exist
for i in hiera ssh_keys certs; do
    [ -d ${BUILD}/$i ] || mkdir -p ${BUILD}/$i
done

cp sfconfig.yaml ${BUILD}/hiera/
generate_hosts_yaml

# Generate site specifics configuration
if [ ! -f "${BUILD}/generate.done" ]; then
    mkdir -p /var/log/edeploy
    echo "PROFILE=none" >> /var/log/edeploy/vars
    generate_keys
    generate_apache_cert
    generate_creds_yaml
    echo -n ${REFARCH} > ${BUILD}/refarch
    touch "${BUILD}/generate.done"
else
    # During upgrade or another bootstrap rup, reuse the same refarch
    [ -f ${BUILD}/refarch ] && REFARCH=$(cat ${BUILD}/refarch)
fi


function wait_for_ssh {
    local ip=$1
    echo "[bootstrap][$ip] Waiting for ssh..."
    while true; do
        KEY=`ssh-keyscan -p 22 $ip`
        if [ "$KEY" != ""  ]; then
            ssh-keyscan $ip | tee -a "$HOME/.ssh/known_hosts"
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
    # Update local /etc/hosts
    echo "[bootstrap] Applying hosts.pp"
    puppet apply --test --environment sf --modulepath=/etc/puppet/environments/sf/modules/ hosts.pp
}

function puppet_apply {
    host=$1
    manifest=$2
    echo "[bootstrap][$host] Applying $manifest"
    ssh -tt root@$host puppet apply --test --environment sf --modulepath=/etc/puppet/environments/sf/modules/ $manifest
    res=$?
    if [ "$res" != 2 ] && [ "$res" != 0 ]; then
        echo "[bootstrap][$host] Failed ($res) to apply $manifest"
        exit 1
    fi
}

function puppet_copy {
    host=$1
    echo "[bootstrap][$host] Copy puppet configuration"
    rsync -a --delete /etc/puppet/ ${host}:/etc/puppet/
}

echo "Boostrapping $REFARCH"
domain=$(cat ${BUILD}/hiera/sfconfig.yaml | grep '^domain:' | awk '{ print $2 }')
# Apply puppet stuff with good old shell scrips
case "${REFARCH}" in
    "1node-allinone")
        prepare_etc_puppet
        puppet_apply_host
        wait_for_ssh "managesf.${domain}"
        puppet_apply "managesf.${domain}" /etc/puppet/environments/sf/manifests/1node-allinone.pp
        ;;
    "2nodes-jenkins")
        # Prepare environment
        sed -i "s/jenkins\.\([^1]*\)192.168.135.101/jenkins.\1192.168.135.102/" ${BUILD}/hiera/hosts.yaml
        prepare_etc_puppet
        puppet_apply_host
        wait_for_ssh "managesf.${domain}"
        wait_for_ssh "jenkins.${domain}"
        puppet_copy jenkins.${domain}

        # Run puppet apply
        puppet_apply "managesf.${domain}" /etc/puppet/environments/sf/manifests/2nodes-sf.pp
        puppet_apply "jenkins.${domain}" /etc/puppet/environments/sf/manifests/2nodes-jenkins.pp
        ;;
    *)
        echo "Unknown refarch ${REFARCH}"
        exit 1
        ;;
esac
echo "SUCCESS ${REFARCH}"
exit 0

# Apply puppet stuff with fancy but broken ansible
#cd ansible;
#exec ansible-playbook -i ${REFARCH}-hosts ${REFARCH}-playbook.yaml
