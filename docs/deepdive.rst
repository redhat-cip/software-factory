Contents:

.. toctree::

Software Factory Deep Dive
==========================

The goal of this document is to describe SF internals.


The image
.........

SF release is actually a new disk image with *everythings* included.
The build_image.sh script does the following:

* The first step fetchs all sub projects such as the managesf service or the python client.
* The second step builds the image cache (see image/softwarefactory.install)
  * Install yum.repos and already packaged requirements
  * Install gerrit (which is build using image/packages/gerrit/build.sh)
  * Install redmine
  * Everything that is not developped by/for SF
* The third step adds the SF secret sauce to the image cache (see image/sf.install)
  * Copy the puppet/ansible modules
  * Install zuul/nodepool
  * Install SF components such as managesf
  * Everything that is developped for SF
* The last step produces a tarball and a qcow2 disk image

Why use an image ?

* Easy install of non packaged services such as gerrit or redmine
* Reproducible deployment (no network access required)
* Reproducible upgrade


The deployment
..............

The image is deployment agnostic since all services are pre-installed but not configured.
Different architectures are supported through a notion of REFARCH.
Here is how an all-in-one deployment works:

* Start the image and wait for ssh access
* Run the sfconfig.sh script to configure services

Multi-node deployment needs multiple instance to be started:

* deploy/lxc/deploy.py will do that automatically with hardcoded local IP address
* deploy/heat/ could support a dynamic inventory (WIP)
* The configuration scripts only needs to know about IP address of other instances

How are services configured ?


The system configuration
........................

The sfconfig.sh script drive the configuration of all services, running from the managesf node it will:

* Set all virtual hosts according to the refarch (e.g. jenkins.fqdn)
* Generate deployment secrets (internal user password, ssh keys and ssl certificates)
* Wait for ssh access to all instances
* Copy puppet configuration
* Run puppet on each host
* Run ansible to orchestrate final configuration (such as the config-repo creation)

System configuration includes external authentication backend and cloud provider, so that all secrets and
service tunning are defined in a single configuration file: sfconfig.yaml. This hiera file will be consumed
by puppet and ansible.

That system configuration process is re-entrant and needs to be executed everytime settings are changed.
For example, if you want to remove redmine from topmenu, edit the sfconfig.yaml value of topmenu_hide_redmine
and execute the sfconfig.sh script.

SF is meant to be a self-service system, thus project configuration is done through the config-repo.


The config-repo
...............

Once SF is up and running, the actual configuration of the CI happens in the config-repo:

* Jenkins jobs are defined in jobs/ jjb configuration
* CI gating is defined in zuul/ zuul layout
* Slave configuration is defined in nodepool/ nodepool configuration (image definition and labels)

This is actually managed through SF CI system, thanks to the config-update job.
This job is actually an ansible playbook that will:

* Reconfigure each jenkins using jenkins-jobs-builder
* Reload zuul configuration (hot reload without losing in-progress tasks)
* Reload nodepool configuration


SF upgrade
..........

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
