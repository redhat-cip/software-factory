#!/bin/sh

ACTION=${SSH_ORIGINAL_COMMAND:-sf_configrepo_update}

if [ "${ACTION}" == "/usr/local/bin/sf-config-update.sh" ]; then
        # Retro compatibility with 2.2.2
        ACTION=sf_configrepo_update
fi
case $ACTION in
    sf_configrepo_update)
        exec ansible-playbook /etc/ansible/sf_configrepo_update.yml
        ;;
    sf_mirror_update)
        exec ansible-playbook -v /etc/ansible/roles/sf-mirror/files/update_playbook.yml
        ;;
    *)
        echo "NotImplemented"
        exit -1
esac
