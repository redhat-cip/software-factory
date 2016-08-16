Configure GIT repository replication
====================================

The replication
---------------

Software Factory provides a feature to keep in sync GIT mirrors on
remote servers. The feature relies on the replication plugin of Gerrit
and is tightly integrated with the Software factory workflow.

In the same spirit of the job' definitions, the replication is configured
through the config repository. Under the directory
"gerrit" you will find a file called replication.config. This file
needs to be modified to setup the replication of one or
several projects.

The replication of project should be done through the SSH protocol and
by default Software Factory will use its own SSH private key to
authenticate against the remote server.


Configure the replication for a project
---------------------------------------

As a project's maintainer, I want to setup the replication of my projects
myproject-client and myproject-server to a remote server. So I have to submit
a patch to the config repository.

Checkout the config repository.

.. code-block:: bash

 $ git clone http://{sf-gateway}/r/config

Edit the file *gerrit/replication.config* and add the following::

 [remote "example-mirror"]
     url = sf@mirrors.domain.example:/home/mirror/git/${name}.git
     mirror = true
     projects = ^myproject-.*

Here we configure the replication plugin of Gerrit to replicate projects
where names match the regular expression "^myproject-.*" to the remote
server mirrors.domain.example. The special placeholder "${name}" is needed here
because the regular expression will match several projects. Furthermore please
note the "mirror" option is used to replicate branch deletion.

Please have a look to the options supported by the plugin
`Replication README </r/plugins/replication/Documentation/config.html>`_.

Then commit and send the patch to Gerrit.

.. code-block:: bash

 $ git commit -m'Add replication for myproject suite'
 $ git review

Then the patch needs to be reviewed and approved by CORE or PTL members
of the config repository. Once your patch is merged the *config-update*
will trigger the replication to mirrors.domain.example (in that example).

**Note:** the SF public key for the replication needs to be added to
the *.ssh/authorized_keys* of the sf user on mirrors.domain.example. Please
request that public to your SofwareFactory admin.

**Note:** if mirrors.domain.example has never been used as a replication
target for Software Factory then your SF admin should add the server's
host key to the known_hosts file.

**Note:** there isn't any need to create the bare GIT repository on the
remote server (as long as a regular shell is available on the target). The
replication plugin will create the repository if it does not exist.


Recommendations for the replication on GitHub
---------------------------------------------

There are two solutions you may use to replicate on Github:

 * Define a deploy key in your project' settings
 * Add a collaborator to you project' setting

The former is less straigtforward than the latter but will work as
expected but will involve more work from the SF administrator. Indeed
the replication plugin will by default uses its own key to authenticate
against your remote (here GitHub). Howerver each deploy key on GitHub
need to be unique so you will have to create key pair and request your
SF admin to install the private part of the key pair on SF.

The latter does not require any specific configuration from
the SF administrator. As a Github project owner you should add a collaborator
(with the Software Factory key registred in the SSH key section of the
Github user settings). SF will then acts on behalf of that Github User for
the replication. Please ask your SF admin if a specific user on Github already
exists.

**Note:** SF won't create repositories on Github if they does not exist. They
should be created manually.


SofwareFactory admin related tasks for the replication
------------------------------------------------------

Below are some explanations and common tasks for a SF admin
related to the replication.


Public key to provide to SF users for the replication
.....................................................

You should expose the Gerrit public SSH key to your users
in order to let them configure the replication target to authorize
SF to authenticate and replicate.

You will find the key at this path::

 /home/gerrit/site_path/etc/ssh_host_rsa_key.pub


Add the host key of the remote server to the known_hosts
........................................................

The gerrit replication plugin expects to validate the remote's
host key. It will look at /home/gerrit/.ssh/known_hosts. If the
replication issue is "Host key rejected" from the log file
/home/gerrit/site_path/logs/replication.log then::

 $ ssh-keyscan <hostname> 2> /dev/null >> /home/gerrit/.ssh/known_hosts


Define a deploy key inside Software Factory
...........................................

In order to configure Gerrit to use a specific deploy key you have to
edit the file /home/gerrit/.ssh/config. The following statements
will force Gerrit to use the key named *deploy-key.pub* for
the host named "github-host-p1-alias"::

 Host "github-host-p1-alias"
 IdentityFile /home/gerrit/.ssh/deploy-key.pub
 PreferredAuthentications publickey
 Hostname github.com

Be sure the host is called by its alias inside replication.config in
order to have this configuration taken in account. Be sure the key is
copied to the right place and own the correct rights.

SF bundles a small utility that help you do that in one command

.. code-block:: bash

 $ cat deploy-key.pub | ssh root@sftests.com gerrit_repl_alias_helper.py \
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
