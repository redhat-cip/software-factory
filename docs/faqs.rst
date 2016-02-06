Contents:

.. toctree::

Frequently Asked Questions
==========================

What is edeploy ?
.................

Edeploy is a (legacy) tool to manage deployment of image based system.
It build and manage the lifecycle of an image that comes with everything
pre-installed so that the whole system can be verified and tested
without Internet access. That means each new changes results in a new
image that has been continuously tested through:

* a full deployment + functional tests
* an upgrade test based on the previous version
* an openstack integration test based on rdo where nodepool and swift
  artifacts export features are tested.


What is the added value of Software Factory ?
.............................................

* Ready to use CI system that works out of the box
* System configuration interface using yaml and puppet/ansible
* Project configuration interface using code review to manage
  jobs, zuul layouts and nodepool project configuration
* REST API to manage project creation and users ACL provisioning
* SSO with ldap/github/launchpad/keystone authentication backend
* Backup and automatic upgrade mechanism (fully tested in sf CI)
* Baremetal, LXC, KVM or OpenStack based deployment
* Fast reproducible setup (3/5 minutes with lxc, 15 minutes with heat)
* Openstack integration to run slave (nodepool) and store artifacts (swift)


Why sf integrates redmine and can it be disabled ?
..................................................

SF goal is to propose a complete workflow to produce software,
including an issue tracking system integrated with the ci workflow.

However since most development team already have an issue tracker,
an on-going effort to support external issue tracker is still in progress.
The main challenge is to do functional testing using mocked resources
to simulate an external tracker.


Why my job fails with "NOT_REGISTERED" error ?
..............................................

This error happens when zuul can't run a job. This means a project
gate have been configured with unknown jobs. Make sure to edit both
jobs and zuul configuration from the config repos.

The first step to investigate that error is to verify the job is active
in jenkins dashboard. If the job is not there, check the config-repo and check
if the job is either expanded from a job-template (using project name), or
either the project is fully defined. Otherwise add the job and update
the config repo.


Why my job stays in "queued" ?
.............................

This happens when no slaves are available to execute a job:

* First check that slaves are attached to jenkins using the dashboard
  (slaves are shown in the left column)
* Then verify node labels are corresponding between slave and jjb definition.


What to do if nodepool is not working ?
.......................................

Until this is provided as an automatic task, here is the manual process:

* Check OpenStack provider tenants and clean left-over resources:
 * server with an uptime more than 12 hours
 * glance images
 * unused floating ip

* Remove un-assigned floating-ip
* Check nodepool logs for permission errors or api failure
* Try to update image manually using:
  nodepool image-update <provider_name> <image_name>

If nothing works, this is how to reset the service:
* Stop nodepoold process
* Delete all OpenStack nodepool resources
* Connect to mysql and delete from node, snapshot_image tables
* Manually update image using:
  nodepool image-update <provider_name> <image_name>
* Start nodepoold process
* Follow the logs and wait for servers to be created.
* Check zuul log to verify it is submitting job request.
