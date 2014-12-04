#!/bin/bash

set -x

wanted=$1
[ -n "$2" ] && infunc_test=true || infunc_test=false

clone_path=/srv/software-factory
[ ! -d "$clone_path" ] && exit 1

# Check that we are able to jump on the request tag (SF version)
cd $clone_path && git checkout $wanted || {
    echo "$wanted version does not exist yet ! exit"
    if [ "$infunc_test" = "false" ]; then
        exit 1
    else
        echo "The upgrade is run in a functional test case. The"
        echo "TAG $wanted does not exist yet. That's normal we can"
        echo "continue."
    fi
}

# Within the tag check we will be able to upgrade the current running SF version
source role_configrc
current_version=$(edeploy version | cut -d'-' -f2)
echo "Detected version is $current_version"
[ "$current_version" != "${PREVIOUS_SF_REL}" ] && {
    echo "The current version of Software Factory running here"
    echo "cannot be upgraded. Whitin this TAG $wanted we are only able to"
    echo "upgrade from ${PREVIOUS_SF_REL} to ${SF_REL}"
    exit 1
}

# get the domain from sfconfig.yaml
DOMAIN=$(egrep "^domain:" /etc/puppet/hiera/sf/sfconfig.yaml | sed 's/domain://' | tr -d ' ')

# Start the upgrade by jumping in the cloned version and running
# the ansible playbook.
cd ${clone_path}/upgrade/${PREVIOUS_SF_VER}/${SF_VER}/
cp group_vars/all.tmpl group_vars/all
sed -i "s/FROM/${PREVIOUS_SF_VER}/" group_vars/all
sed -i "s/TO/${SF_VER}/" group_vars/all
sed -i "s/DOMAIN/${DOMAIN}/" group_vars/all
sed -i "s|CLONE_PATH|${clone_path}|" group_vars/all
ansible-playbook -i hosts site.yml
echo "Ansible return code is : $?"
cd -
