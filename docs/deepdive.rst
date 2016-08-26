Software Factory Internals
==========================

The goal of this document is to describe SF internals.


The components
--------------

Below is an overview of all the components integration (shown as dashed boxes) and services
along with their connections to each others.

.. graphviz:: components.dot


The SSO mechanism
-----------------

Below is the sequence diagram of the SSO mechanism.

.. graphviz:: authentication.dot


The image
---------

SF release is actually a new disk image with *everythings* included.
The build_image.sh script does the following:

* The first step fetchs all sub projects such as the managesf service or the python client.
* The second step builds the image cache (see image/softwarefactory.install)

  * Install yum.repos and already packaged requirements
  * Install gerrit (which is build using image/packages/gerrit/build.sh)
  * Install zuul/nodepool
  * Install redmine
  * Everything that is not developped by/for SF

* The third step adds the SF secret sauce to the image cache (see image/sf.install)

  * Copy the puppet/ansible modules
  * Install SF components such as managesf
  * Everything that is developped for SF

* The last step produces a tarball and a qcow2 disk image

Why use an image ?

* Easy install of non packaged services such as gerrit or redmine
* Reproducible deployment (no network access required)
* Reproducible upgrade


The deployment
--------------

The image is deployment agnostic since all services are pre-installed but not configured.
Different architectures are supported through a notion of REFARCH.
Here is how an all-in-one deployment works:

* Start the image and wait for ssh access
* Run the sfconfig.sh script to configure services

Multi-node deployment needs multiple instance to be started:

* deploy/lxc/deploy.py will do that automatically with hardcoded local IP address
* deploy/heat/ could support a dynamic inventory (WIP)
* The configuration scripts only needs to know about IP address of other instances

Next sections cover how services are configured.


The system configuration
------------------------

The sfconfig.sh script drives the system configuration. This script does the following actions:

* Generates secrets such as ssh keys and tls certificats,
* Generates sfcreds.yaml system credencials such as service database access and api keys,
* Run sf-update-hiera-config.py to ensure hieras are up-to-date, this script
  checks for missing section and makes sure the defaults value are present. This is particularly
  useful when after an upgrade, a new component configuration has been added
* Generates Ansible inventory and configuration playbook based on the arch.yaml file.
* Waits for ssh access to all instances
* Run sf_setup.yml playbook to setup all the services and run puppet when needed. This executes
  all the setup.yml task of enabled ansible roles.
* Run sf_initialize.yml playbook. This creates the config-repo and run the sf_configrepo_update.yml playbook
  to update services based on config repo content.
* Run sf_postconf.yml playbook to executes all the postconf.yml task of enabled ansible roles such as
  the mirror role postconf that can enables a new periodic pipeline

That system configuration process is re-entrant and needs to be executed everytime settings are changed.
For example, to remove redmine from topmenu, edit the sfconfig.yaml value of topmenu_hide_redmine
and execute the sfconfig.sh script.

Then SF is meant to be a self-service system, thus project configuration is done through the config-repo.


The config-repo
---------------

Once SF is up and running, the actual configuration of the CI happens in the config-repo:

* jobs/: Jenkins jobs jjb configuration,
* zuul/: CI gating zuul yaml configuration,
* nodepool/: Slave configuration with images and labels definitions,
* gerritbot/: IRC notification for gerrit event configuration,
* gerrit/: Gerrit replication endpoint configuration, and
* mirrors/: mirror2swift configuration.

This is actually managed through SF CI system, thanks to the config-update job.
This job is actually an ansible playbook that will:

* Reconfigure each jenkins using jenkins-jobs-builder,
* Reload zuul configuration (hot reload without losing in-progress tasks),
* Reload nodepool, gerritbot and gerrit replication, and
* Set mirror2swift configuration for manual or next periodic update.


The upgrade
-----------

The upgrade procedure is not included in the image, and the operator needs to manually download
the module. It is part of software-factory project repository and the wanted tag release, based
on the role_configrc commited in the tag, it will:

* Download new version image
* Stop all services
* Copy the new image in-place using rsync
* Execute upgrade task (such as database migration or system-level change such as permission change)
* Execute the sfconfig.sh script
* Check deployment

To be sure the system is consistent, rsync will erase all foreign file except the one in the exclude
list (image/softwarefactory.exclude). All state date such as git repository are conserved while
non-managed bits will be removed.
