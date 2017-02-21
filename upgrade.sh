#!/bin/bash

REFARCH=${1:-1node-allinone}

. role_configrc
cloned_path=$(pwd)
current_version=$(edeploy version)
[ "$current_version" == "${SF_VER}" ] && {
    echo "Already upgraded"
    exit 1
}
echo "Going to upgrade from $current_version to ${SF_VER}"
if [ ! -d "./upgrade/${current_version}" ]; then
    echo "Upgrade path is not supported"
    exit 1
fi

# set PATH
export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# fix rsyncd install dir
[ -d /var/lib/debootstrap ] || mkdir /var/lib/debootstrap
[ -e /var/lib/debootstrap/install ] && rm -Rf /var/lib/debootstrap/install
ln -s /var/lib/sf/roles/install/ /var/lib/debootstrap/install

set -x
# Start the upgrade by jumping in the cloned version and running
# the ansible playbook.
cd ./upgrade/${current_version}/${SF_VER}/ || exit -1
cp group_vars/all.tmpl group_vars/all
sed -i "s/FROM/${current_version}/" group_vars/all
sed -i "s/TO/${SF_VER}/" group_vars/all
sed -i "s|CLONE_PATH|${cloned_path}|" group_vars/all

echo "[+] Running step1.yaml"
ansible-playbook step1.yaml
STEP1_RETURN_CODE=$?
echo "Ansible return code is : ${STEP1_RETURN_CODE}"
[ ${STEP1_RETURN_CODE} != "0" ] && exit -1
# Ansible package may change during the upgrade (FS rsync) so we do the update in two steps
echo "[+] Running step2.yaml"
ansible-playbook step2.yaml
STEP2_RETURN_CODE=$?
echo "Ansible return code is : ${STEP2_RETURN_CODE}"
[ ${STEP2_RETURN_CODE} != "0" ] && exit -1

# Step2 setup global group_vars, run the last step
echo "[+] Running step3.yaml"
ansible-playbook step3.yaml
STEP3_RETURN_CODE=$?
echo "Ansible return code is : ${STEP3_RETURN_CODE}"
[ ${STEP3_RETURN_CODE} != "0" ] && exit -1

exit 0
