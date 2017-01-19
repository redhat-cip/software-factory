.. _gerritbot-operator:

Configure gerritbot for IRC notification
----------------------------------------

To start the service:

* Add the gerritbot role to desired host in the inventory: /etc/software-factory/arch.yaml:

.. code-block:: yaml

  inventory:
    - hostname: managesf.sftests.com
      roles:
        - gerritbot

* Set the gerritbot configuration in /etc/software-factory/sfconfig.yaml:

.. code-block:: yaml

  gerritbot:
    botname: sfbot
    disabled: false

* Re-apply: sfconfig.py

Then finish the configuration with the :ref:`user configuration <gerritbot-user>`
