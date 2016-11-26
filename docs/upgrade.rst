Upgrade Software Factory
========================

What is an upgrade of a Software Factory instance
-------------------------------------------------

As you already know Software Factory eases the deployment of a Continous Integration
platform by allowing you to deploy such a platform within a couple of minutes but
an important point is how I maintain this platform up to date ?

- Latest version of Software Factory workflow.
- Most recent stable version of components like (Jenkins, Gerrit, JJB, Redmine, ...).
- Most recent base OS packages (libraries, kernel, ...).

Software Factory being image-based, each new releases provides a new set of image to be used
either for new deployment, or to upgrade an existing one.

Indeed the main mechanism behind a Software Factory upgrade is the (rsync) copy of the
files system diff between the running instance and the image reference. This copy
can be performed without shutting down nodes that compound a Software
Factory deployment.

The steps involved during an upgrade:

- Connect via ssh to the managesf node
- Clone the SF repository
- Start the upgrade.sh script with the wanted version as argument.

The upgrade script will:

- Checkout the wanted version (TAG) of Software Factory.
- Fetch the SF image of the version.
- Stop all SF components (Gerrit, Jenkins, ...)
- Live copy the file system diff using rsync.
- Trigger ansible apply.
- Auto submit a new Review to Gerrit config repository if the upgrade
  bring modifications for the default JJB and Zuul base files.


What about the existing data in your SF instance during an upgrade
------------------------------------------------------------------

The files system upgrade done via rsync takes care of directories where user data
are. That means user data are kept on the node and untouched by the upgrade
process. Nevertheless if a component upgrade requires a user data format upgrade
then the SF upgrade system take care of that.


How I upgrade my SF instance
----------------------------

Before each upgrade you should perform a backup of all user data using the backup system
of Software Factory. (:ref:`managesf_backup`)

Here are the steps to upgrade:

.. code-block:: bash

 $ ssh root@fqdn
 $ git clone http://softwarefactory-project.io/r/software-factory software-factory
 $ cd software-factory
 $ git checkout <latest TAG>
 $ ./upgrade.sh

A change (named "Upgrade of base config repository files") for the config repository
may be proposed as a review on Gerrit when some default files have evolve between both
version of SF. You should take care of approving that change to avoid unexpected
behaviors on the validation or apply phases of config repository changes.
