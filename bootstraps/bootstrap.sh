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

SF_SUFFIX=${SFSUFFIX:-tests.dom}
BUILD=/root/sf-bootstrap-data

# Make sure sf-bootstrap-data sub-directories exist
for i in hiera ssh_keys certs; do
    [ -d ${BUILD}/$i ] || mkdir -p ${BUILD}/$i
done

# Generate site specifics configuration
generate_keys
generate_creds_yaml
generate_hosts_yaml
generate_sfconfig

if [ ! -e "${BUILD}/certs/gateway.key" ]; then
    generate_apache_cert
fi

# Move site specific file to puppet/modules/*/files/
prepare_etc_puppet

# Apply puppet stuff
set +e
puppet apply --test --environment sf --modulepath=/etc/puppet/environments/sf/modules/ /etc/puppet/environments/sf/manifests/site.pp
[ "$?" != 2 ] && exit 1
exit 0
