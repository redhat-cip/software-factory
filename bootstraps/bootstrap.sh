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

SF_SUFFIX=${SF_SUFFIX:-tests.dom}
BUILD=/root/sf-bootstrap-data
REFARCH=${1:-1node-allinone}

# Make sure sf-bootstrap-data sub-directories exist
for i in hiera ssh_keys certs; do
    [ -d ${BUILD}/$i ] || mkdir -p ${BUILD}/$i
done

# Generate site specifics configuration
if [ ! -f "${BUILD}/generate.done" ]; then
    mkdir -p /var/log/edeploy
    echo "PROFILE=none" >> /var/log/edeploy/vars
    generate_keys
    generate_creds_yaml
    generate_hosts_yaml
    generate_sfconfig
    generate_apache_cert
    touch "${BUILD}/generate.done"
fi


function wait_for_ssh {
    local ip=$1
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

function puppet_apply {
    host=$1
    manifest=$2
    echo "[bootstrap][$host] Applying $manifest"
    ssh -tt root@$host puppet apply --test --environment sf --modulepath=/etc/puppet/environments/sf/modules/ $manifest
    res=$?
    if [ "$res" != 2 ] && [ "$res" != 0 ]; then # && [ "$res" != 6 ]; then
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
# Apply puppet stuff with good old shell scrips
case "${REFARCH}" in
    "1node-allinone")
        prepare_etc_puppet
        wait_for_ssh "managesf.${SF_SUFFIX}"
        puppet_apply "managesf.${SF_SUFFIX}" /etc/puppet/environments/sf/manifests/1node-allinone.pp
        ;;
    "2nodes-jenkins")
        # Prepare environment
        sed -i "s/jenkins\.\([^1]*\)192.168.135.101/jenkins.\1192.168.135.102/" ${BUILD}/hiera/hosts.yaml
        prepare_etc_puppet
        wait_for_ssh "managesf.${SF_SUFFIX}"

        # Run puppet apply
        puppet_apply "managesf.${SF_SUFFIX}" /etc/puppet/environments/sf/manifests/2nodes-sf.pp
        wait_for_ssh "jenkins.${SF_SUFFIX}"
        puppet_copy jenkins.${SF_SUFFIX}
        puppet_apply "jenkins.${SF_SUFFIX}" /etc/puppet/environments/sf/manifests/2nodes-jenkins.pp
        ;;
    "*")
        echo "Unknown refarch ${REFARCH}"
        exit 1
        ;;
esac
echo "SUCCESS ${REFARCH}"
exit 0

# Apply puppet stuff with fancy but broken ansible
#cd ansible;
#exec ansible-playbook -i ${REFARCH}-hosts ${REFARCH}-playbook.yaml
