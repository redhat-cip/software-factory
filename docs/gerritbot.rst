.. toctree::

Configure gerritbot for IRC notification
========================================

System configuration
--------------------

To start the service:

* Add the gerritbot role to desired host in the inventory: /etc/puppet/hiera/sf/arch.yaml::

  inventory:
    - hostname: managesf.sftests.com
      roles:
        - gerritbot

* Set the gerritbot configuration in /etc/puppet/hiera/sf/sfconfig.yaml::

  gerritbot:
    botname: sfbot
    disabled: false

* Re-apply: sfconfig.sh


Project configuration
---------------------

Once the service is running, you can configure the irc channels to get notification:

* git clone the config-repository
* add a new file or edit one in config/gerritbot directory::

  irc-channel-name:
    events:
      - change-created
      - change-merged
    projects:
      - myproject
    branches:
      - master

* submit and merge the config change.
* the gerritbot will be updated once the config-update job succeed.
