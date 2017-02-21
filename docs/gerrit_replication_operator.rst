.. _gerrit-replication-operator:

Gerrit GIT repositories replication
===================================

Sofware Factory admin related tasks for the replication
-------------------------------------------------------

Below are some explanations and common tasks for a SF admin
related to the replication.

See the :ref:`Gerrit replication user documentation<gerrit-replication-user>`


Public key to provide to SF users for the replication
.....................................................

You should expose the Gerrit public SSH key to your users
in order to let them configure the replication target to authorize
SF to authenticate and replicate.

You will find the key at this path::

 /etc/gerrit/ssh_host_rsa_key.pub


Add the host key of the remote server to the known_hosts
........................................................

The gerrit replication plugin expects to validate the remote's
host key. It will look at /var/lib/gerrit/.ssh/known_hosts. If the
replication issue is "Host key rejected" from the log file
/var/log/gerrit/replication.log then::

 $ ssh-keyscan <hostname> 2> /dev/null >> /var/lib/gerrit/.ssh/known_hosts


Define a deploy key inside Software Factory
...........................................

In order to configure Gerrit to use a specific deploy key you have to
edit the file /var/lib/gerrit/.ssh/config. The following statements
will force Gerrit to use the key named *deploy-key.pub* for
the host named "github-host-p1-alias"::

 Host "github-host-p1-alias"
 IdentityFile /var/lib/gerrit/.ssh/deploy-key.pub
 PreferredAuthentications publickey
 Hostname github.com

Be sure the host is called by its alias inside replication.config in
order to have this configuration taken in account. Be sure the key is
copied to the right place and own the correct rights.

SF bundles a small utility that help you do that in one command

.. code-block:: bash

 $ cat deploy-key.pub | ssh root@fqdn gerrit_repl_alias_helper.py \
   --hostname github.com --key-from-stdin github-host-p1-alias

or

.. code-block:: bash

 $ gerrit_repl_alias_helper.py --hostname github.com --key-path \
   /tmp/deploy-key.pub github-host-p1-alias

These commands will copy the key at the right place and populate
.ssh/config correctly.


Restart the Gerrit replication plugin
.....................................

If a modification in .ssh/config or .ssh/known_hosts is not taken
in account by the Gerrit replication plugin then you will need to
reload and restart the replication with the following commands.

.. code-block:: shell

 $ ssh -p 29418 admin@sftests.com gerrit plugin reload replication
 $ ssh -p 29418 admin@sftests.com replication start --all


General recommendations for the replication on GitHub
.....................................................

If some of your users plan to replicate GIT repositories on Github it
can be useful to create a specific SF user on Github with the Gerrit
public key registered to this user's setting. This user will
be the Github identity of your SF deployment. Each SF's user will
only need to add this user as a project's collaborator.
