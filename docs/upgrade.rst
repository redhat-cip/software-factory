.. toctree::

Upgrade Software Factory
========================

What is an upgrade of a Software Factory instance
-------------------------------------------------

As you already know Software Factory eases the deployment of a Continous Integration
platform by allowing you to deploy such a platform within a couple of minutes but
an important point is how I maintain this platform up to date ?

By up to date we mean:

- Usage of the lastest version of Software Factory workflow.
- Usage of the most recent stable version of components like (Jenkins, Gerrit, JJB, Redmine, ...).
- Usage of the most recent base OS packages (librairies, kernel, ...).

Software Factory being image-based, each new releases provides a new set of image to be used
either for new deployment, or to upgrade an existing one.

Indeed the main mechanism behind a Software Factory upgrade is the (rsync) copy of the
files system diff between a running instance and the images reference. This copy
can be performed without shutting down Virtual nodes that compound a Software
Factory deployment.

The steps involved during an upgrade:

- Connect via ssh to the puppetmaster node of the SF deployment.
- Clone the SF repository in a specific directory.
- Start the upgrade.sh script with the wanted version as argument.

The upgrade script will:

- Checkout the wanted version (TAG) of Software Factory.
- Fetch the SF images related to the tagged SF version.
- Stop all SF components (Gerrit, Jenkins, ...)
- Run the live copy of the file system diff between the new images and the running
  system on each nodes.
- Trigger puppet agents on each node and apply changes if needed.
- Auto submit a new Review to Gerrit config repository if the upgrade
  bring modifications for the default JBB and Zuul base files.

What about the existing data in your SF instance during an upgrade
------------------------------------------------------------------

The files system upgrade done via rsync take care of directories where user data
are. That means user data are kept on the node and untouched by the upgrade
process. Nevertheless if a component upgrade requires a user data format upgrade
then the SF upgrade system take care of that.

How I upgrade my SF instance
----------------------------

We only support upgrade from latest TAG-1 to the latest TAG. And we encourage to
upgrade an already deployed SF platform at each new version.

Before each upgrade you should perform a backup of all user data using the backup system
of Software Factory. (:ref:`CreateBackupCli`)

Here are the steps to upgrade:

.. code-block:: bash

 $ ssh root@puppetmaster_public_address
 $ git clone http://softwarefactory.enovance.com/r/software-factory /srv/software-factory
 $ cd /srv/software-factory
 $ ./upgrade.sh <latest TAG>

Upgrade are tested in our CI
----------------------------

The upgrade scenario for the latest SF TAG to the future TAG is tested in our CI before
we release that future TAG of Software Factory. In order to test an upgrade
we deploy the latest TAG of SF, we provision it with fake user data then we start
the upgrade to the current master (the future SF TAG) and finally we check that
provisionned user data are still present and that all SF components behave as expected.
