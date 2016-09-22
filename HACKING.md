Software Factory coding guidelines
==================================

This is a list of good practices to fix and follow:

# System

## Service user

* Do not use root user to run a service or action of any kind.
  Instead always create a user:
    - include: /etc/ansible/tasks/create_user.yml user_name=mirror2swift

  Then either configure the service to run as this user, either
  perform ansible task using:
    - name: "Update mirrors"
      become: true
      become_user: mirror2swift
      command: mirror2swift --update /var/lib/mirror2swift/config.yaml

## Directories and file permission

* Logs shall be written to /var/log
* Service state data shall be written to /var/lib
* Most file do not need write permission, use 0444 for regular and 0555 for executable.
  This adds a nice extra layer of protection against invalid modification.
* Never give ownership to the service user unless the file can be edited. Always use root:root.
* When a configuration contain secret, use 0440 with root:$servicename

## Run action as root

* Do not use sudo, instead reproduces the config-update job process, e.g.:
  * Use a copy of the jenkins_rsa key
  * Add the action to sf-config-update.sh
  * Run ssh root@install-server.$fqdn $action_name


# Configuration

## sfconfig.yaml

* When an option is added or removed, also update the sf-update-hiera-config.py script.

## config-repo.yaml

* When a file is added or removed, also add an upgrade task (check policy_configrepo.yml)
