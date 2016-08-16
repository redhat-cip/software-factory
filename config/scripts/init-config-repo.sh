#!/bin/bash
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

set -x
set -e

[ "$1" = "upgrade" ] && upgrade=true || upgrade=false

gateway_host="$2"
gateway_url="http://$2"

auth="admin:$3"

gerrit_ssh_key="/root/sf-bootstrap-data/ssh_keys/gerrit_admin_rsa"

if [ "$upgrade" = "false" ]; then
    # Create config project (managesf must be up)
    if [ ! -f '/usr/share/config.init.done' ]; then
        sfmanager --url $gateway_url --auth $auth project create --name config --description "Config repository (Do not delete it)"
        touch /usr/share/config.init.done
    fi
fi

# Clone the config project
echo "ssh -o StrictHostKeyChecking=no -i $gerrit_ssh_key \$@" > /root/ssh_wrapper.sh
chmod +x /root/ssh_wrapper.sh
export GIT_SSH="/root/ssh_wrapper.sh"
CONF_TMP=$(mktemp -d)
git clone ssh://admin@${gateway_host}:29418/config ${CONF_TMP}

if [ "$upgrade" = "false" ]; then
    if [ -d "${CONF_TMP}/jobs" ]; then
        echo "Config repository already initialised"
        rm -rf ${CONF_TMP}
        exit 0
    fi

    # Add default files
    rsync -av /usr/local/share/sf-config-repo/ ${CONF_TMP}/

    # Commit the changes
    cd ${CONF_TMP}
    git add .
    git commit -a -m "Initialize config repository"
    git push origin master
fi

if [ "$upgrade" = "true" ]; then
    rsync --exclude jobs/projects.yaml --exclude zuul/projects.yaml --exclude nodepool/images.yaml --exclude nodepool/labels.yaml \
        --exclude gerrit/replication.config --exclude gerritbot/channels.yaml -av /usr/local/share/sf-config-repo/ ${CONF_TMP}/
    cd ${CONF_TMP}
    # Replace nodepool private ssh key
    sed -i 's#private-key: /var/lib/jenkins/.ssh/id_rsa#private-key: /var/lib/nodepool/.ssh/id_rsa#' nodepool/images.yaml
    # Only perform the commit/review if the upgrade bring new modifications
    if [ -n "$(git ls-files -o -m --exclude-standard)" ]; then
        git commit -a -m "Upgrade of base config repository files"
        (eval $(ssh-agent) && ssh-add $gerrit_ssh_key && git review -s)
        git review -i
    fi
    cd -

fi
rm -rf ${CONF_TMP}
