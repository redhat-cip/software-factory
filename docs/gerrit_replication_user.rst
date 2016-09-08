.. _gerrit-replication-user:

Configure Gerrit GIT repositories replication
=============================================

The replication
---------------

Software Factory provides a feature to keep in sync GIT mirrors on
remote servers. The feature relies on the replication plugin of Gerrit
and is tightly integrated with the Software Factory workflow.

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

 $ git clone http://<fqdn>/r/config

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
request that public to your Sofware Factory admin.

See the :ref:`Gerrit replication operator documentation<gerrit-replication-operator>`

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
