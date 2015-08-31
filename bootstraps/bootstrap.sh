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

source functions.sh

SF_SUFFIX=${SFSUFFIX:-sf.dom}
BUILD=/root/sf-bootstrap-data

# If boostrap.done does not exist, something bad happened, write 1
trap "[ -f ${BUILD}/bootstrap.done ] || (echo 1 > ${BUILD}/bootstrap.done)" 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
if [  -f "${BUILD}/bootstrap.done" ]; then
    rm ${BUILD}/bootstrap.done
fi

# Make sure sf-bootstrap-data sub-directories exist
for i in hiera ssh_keys certs; do
    [ -d ${BUILD}/$i ] || mkdir -p ${BUILD}/$i
done

# Move sfconfig.yaml installed by cloud-init
[ -f /root/sfconfig.yaml ] && mv /root/sfconfig.yaml /root/sf-bootstrap-data/hiera

if [ "${INITIAL}" == "yes" ]; then
    # Generate site specifics creds
    generate_keys
    generate_creds_yaml
fi

if [ ! -e "${BUILD}/certs/gateway.key" ]; then
    generate_apache_cert
fi

# Move site specific file to puppet/modules/*/files/
prepare_etc_puppet
# Wait for all node SSH service to be up
wait_all_nodes
# Start a run locally and start the puppet agent service
run_puppet_agent
# Force a stop of puppet agent on each roles
run_puppet_agent_stop
# Start a run on each node and start the puppet agent service
trigger_puppet_apply
# Force a start of puppet agent on each roles after a delay that let us run func tests smoosly
run_puppet_agent_start
# Set a witness file that tell the bootstraping is done
echo 0 > ${BUILD}/bootstrap.done
