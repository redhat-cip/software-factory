#!/bin/sh

ACTION=${SSH_ORIGINAL_COMMAND:-sf_configrepo_update}

if [ "${ACTION}" == "/usr/local/bin/sf-config-update.sh" ]; then
        # Retro compatibility with 2.2.2
        ACTION=sf_configrepo_update
fi

case $ACTION in
    sf_configrepo_update)
        exec ansible-playbook /etc/ansible/sf_configrepo_update.yml &> /var/log/software-factory/configrepo_update.log
        ;;
    sf_mirror_update)
        exec ansible-playbook -v /etc/ansible/roles/sf-mirror/files/update_playbook.yml &> /var/log/software-factory/mirror_update.log
        ;;
    sf_backup)
        exec ansible-playbook -v /etc/ansible/sf_backup.yml &> /var/log/software-factory/backup.log
        ;;
    sf_restore)
        exec ansible-playbook -v /etc/ansible/sf_restore.yml &> /var/log/software-factory/restore.log
        ;;
    *)
        echo "NotImplemented"
        exit -1
esac
