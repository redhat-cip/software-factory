.. _config-repo:

=====================
The config repository
=====================

Many parameters are available to the users through the config repository.
The config repository is a special projects to configure many Software Factory services.
This enables users to propose modifications through the code review system,
and after change approval, the config-update job applies configuration change.

To update the configuration repo:

* First clone the repository: git clone http://<fqdn>/r/config
* Edit files and commit: git commit
* Create a review: git review
* Approve the review to run config update

.. note::

  Files starting by a "_" are default settings and they may be modified by
  an upgrade of Software Factory, thus they **shouldn't be modified manually**.


.. toctree::
   :maxdepth: 3

   cicd_intro
   jenkins_user
   zuul_user
   swiftlogs_user
   nodepool_user
   gerritbot_user
   gerrit_replication_user
   access_control_user


