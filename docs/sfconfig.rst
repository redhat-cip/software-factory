.. _sfconfig:

Main configuration file: sfconfig.yaml
======================================

Currently located in /etc/software-factory/sfconfig.yaml,
this is THE SF configuration entry point.

Notice that the configuration is versioned and it is recommended to use git diff and git commit
command to check files modifications.

Ansible roles variable can be over-written in /etc/software-factory/custom-vars.yaml file too.

.. note::

  Any modification to sfconfig.yaml needs to be manually applied with the sfconfig.py script.
  Run sfconfig.py after saving the sfconfig.yaml file.


.. toctree::
   :maxdepth: 3

   fqdn
   auths
   zuul_operator
   swiftlogs_operator
   nodepool_operator
   gerritbot_operator
