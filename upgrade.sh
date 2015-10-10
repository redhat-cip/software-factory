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

# update new default variable
SRC=./config/defaults/sfconfig.yaml
DST=/etc/puppet/hiera/sf/sfconfig.yaml

cp ${DST} ${DST}.orig
if [ ! -f ${SRC} ] || [ ! -e ${DST} ]; then
    echo "Missing configuration file..."
    exit -1
fi
grep -q '^admin_name' ${DST} && {
    echo "[+] sfconfig migration"
    ./config/scripts/migration_sfconfig-2.0.0.py ${DST} ${SRC} || exit -1
}
./config/scripts/validate_sfconfig.py ${DST} || exit -1

# check install files
if [ ! -d "/var/lib/debootstrap/install/${SF_VER}/softwarefactory/" ]; then
    echo "Fetch new version"
    ./fetch_image.sh
    echo "Install files"
    mkdir -p /var/lib/debootstrap/install/${SF_VER}
    ln -s ${IMAGE_PATH}/ /var/lib/debootstrap/install/${SF_VER}/softwarefactory/
fi


set -x
# Start the upgrade by jumping in the cloned version and running
# the ansible playbook.
cd ./upgrade/${current_version}/${SF_VER}/ || exit -1
cp group_vars/all.tmpl group_vars/all
sed -i "s/FROM/${PREVIOUS_SF_VER}/" group_vars/all
sed -i "s/TO/${SF_VER}/" group_vars/all
sed -i "s|CLONE_PATH|${cloned_path}|" group_vars/all

echo "[+] Running ${REFARCH}-step1.yaml"
ansible-playbook -i ${REFARCH}-hosts ${REFARCH}-step1.yaml
STEP1_RETURN_CODE=$?
echo "Ansible return code is : ${STEP1_RETURN_CODE}"
[ ${STEP1_RETURN_CODE} != "0" ] && exit -1
# Ansible package may change during the upgrade (FS rsync) so we do the update in two steps
echo "[+] Running ${REFARCH}-step2.yaml"
ansible-playbook -i ${REFARCH}-hosts ${REFARCH}-step2.yaml
STEP2_RETURN_CODE=$?
echo "Ansible return code is : ${STEP2_RETURN_CODE}"
[ ${STEP2_RETURN_CODE} != "0" ] && exit -1

exit 0
