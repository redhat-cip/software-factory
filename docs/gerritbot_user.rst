.. _gerritbot-user:

Gerritbot notification channels configuration
=============================================

Once the service is running (see :ref:`operator configuration <gerritbot-operator>`),
you can configure the irc channels to get notification:

* git clone the config-repository
* add a new file or edit one in config/gerritbot directory:

.. code-block:: yaml

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
