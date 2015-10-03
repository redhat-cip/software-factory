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

source functions.sh

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
            IP_JENKINS=$OPTARG
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
            echo "an already deploy SF then this is the option you need to use."
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
    # During upgrade or another bootstrap rup, reuse the same refarch
    REFARCH=$(cat ${BUILD}/hiera/sfarch.yaml | sed 's/ //g' | grep "^refarch:" | cut -d: -f2)
    IP_JENKINS=$(cat ${BUILD}/hiera/sfarch.yaml | sed 's/ //g' | grep "^jenkins_ip:" | cut -d: -f2)
    # Support 2.0.0beta
    if [ -f ${BUILD}/refarch ]; then
        REFARCH="$(cat ${BUILD}/refarch)"
    fi
fi

update_sfconfig
puppet_apply_host
echo "[bootstrap] Boostrapping $REFARCH"
# Apply puppet stuff with good old shell scrips
case "${REFARCH}" in
    "1node-allinone")
        wait_for_ssh "managesf.${DOMAIN}"
        puppet_apply "managesf.${DOMAIN}" /etc/puppet/environments/sf/manifests/1node-allinone.pp
        ;;
    "2nodes-jenkins")
        [ "$IP_JENKINS" == "127.0.0.1" ] && {
            echo "[bootstrap] Please select another IP_JENKINS than 127.0.0.1 for this REFARCH"
            exit 1
        }
        wait_for_ssh "managesf.${DOMAIN}"
        wait_for_ssh "jenkins.${DOMAIN}"
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
echo "SUCCESS ${REFARCH}"
exit 0
