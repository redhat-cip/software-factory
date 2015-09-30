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

while getopts ":a:i:d:h" opt; do
    case $opt in
        a)
            REFARCH=$OPTARG
            [ $REFARCH != "1node-allinone" -a $REFARCH != "2nodes-jenkins" ] && {
                    echo "Available REFARCH are: 1node-allinone or 2nodes-jenkins"
                    exit 1
            }
            ;;
        i)
            IP=$OPTARG
            ;;
        d)
            DOMAIN=$OPTARG
            ;;
        h)
            echo ""
            echo "Usage:"
            echo ""
            echo "If run without any options bootstrap script will use defaults:"
            echo "REFARCH=1node-allinone"
            echo "DOMAIN=tests.dom"
            echo ""
            echo "Use the -a option to specify the REFARCH."
            echo ""
            echo "If REFARCH is 2nodes-jenkins then is is expected you pass"
            echo "the ip of the node where the CI system will be installed"
            echo "via the -i option."
            echo ""
            echo "Use -d option to specify under which domain the SF gateway"
            echo "will be installed. If you intend to reconfigure the domain on"
            echo "an already deploy SF then this is the option use need to use."
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


DEBUG=1
source functions.sh

BUILD=/root/sf-bootstrap-data
# Make sure sf-bootstrap-data sub-directories exist
for i in hiera ssh_keys certs; do
    [ -d ${BUILD}/$i ] || mkdir -p ${BUILD}/$i
done

DOMAIN=${DOMAIN:-tests.dom}
sed -i "s/^domain:.*/domain: $DOMAIN/" sfconfig.yaml
cp sfconfig.yaml ${BUILD}/hiera/

# Generate site specifics configuration
if [ ! -f "${BUILD}/generate.done" ]; then
    REFARCH=${REFARCH:-1node-allinone}
    IP=${IP:-127.0.0.1}
    mkdir -p /var/log/edeploy
    echo "PROFILE=none" >> /var/log/edeploy/vars
    generate_keys
    generate_apache_cert
    generate_creds_yaml
    echo -n ${REFARCH} > ${BUILD}/refarch
    echo -n ${IP} > ${BUILD}/ip
    touch "${BUILD}/generate.done"
else
    [ -n "$REFARCH" ] && {
        echo "REFARCH has been already selected. Skipping your choice from options."
    }
    [ -n "$IP" ] && {
        echo "IP has been already selected. Skipping your choice from options."
    }
    # During upgrade or another bootstrap rup, reuse the same refarch
    [ -f ${BUILD}/refarch ] && REFARCH=$(cat ${BUILD}/refarch)
    [ -f ${BUILD}/ip ] && IP=$(cat ${BUILD}/ip)
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
        generate_hosts_yaml "127.0.0.1"
        prepare_etc_puppet
        puppet_apply_host
        wait_for_ssh "managesf.${domain}"
        puppet_apply "managesf.${domain}" /etc/puppet/environments/sf/manifests/1node-allinone.pp
        ;;
    "2nodes-jenkins")
        [ "$IP" = "127.0.0.1" ] && {
            echo "Please select another IP than 127.0.0.1 for this REFARCH"
            exit 1
        }
        generate_hosts_yaml $IP
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
