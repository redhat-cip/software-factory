.. _sfconfig:

Main configuration file: sfconfig.yaml
======================================

Currently located in /etc/software-factory/sfconfig.yaml,
this is THE SF configuration entry point.

Notice that the configuration is versioned and it is recommended to use git diff and git commit
command to check files modifications.

.. note::

  Any modification to sfconfig.yaml needs to be manually applied with the sfconfig.sh script.
  Run sfconfig.sh after saving the sfconfig.yaml file.


.. toctree::
   :maxdepth: 3

   fqdn
   auths
   zuul_operator
   swiftlogs_operator
   nodepool_operator
   gerritbot_operator
