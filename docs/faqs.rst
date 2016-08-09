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

It might happen that some nodes are kept in the "delete" state for quite some
time, while they are already deleted. This blocks spawning of new instances.
The simplest way to fix this is to clean the stale entries in the nodepool DB
using the following command (deleting all entries older than 24 hours and in
state delete):

.. code-block:: mysql

     DELETE FROM node WHERE state_time < (UNIX_TIMESTAMP() - 86400) AND state = 4;

How can I change the hostname?
..............................

You can change the hostname after the deployment by setting the fqdn parameter
in /etc/puppet/hiera/sf/sfconfig.yaml, removing the existing SSL certificates
(only required if runninng functional tests and using the default self-signed
certificates) and running sfconfig.sh again:

.. code-block:: bash

    sed -i -e 's/fqdn:.*/fqdn: mynewhostname.com/g' /etc/puppet/hiera/sf/sfconfig.yaml
    sed -i -e 's/sftests.com/sftests2.com/g' /etc/puppet/hiera/sf/arch.yaml
    rm /root/sf-bootstrap-data/certs/gateway.* /root/openssl.cnf
    sfconfig.sh

Please note that you might need to update URLs in other places as well, for
example git remote urls in .gitreview and .git/config files in repositories
hosted on Software Factory.


How can I use an external gerrit ?
..................................

You can configure zuul to connect to a remote gerrit event stream.
First you need a Non-Interactive Users created on the external gerrit.
Then you need to configure that user to use the local zuul ssh public key:
/var/lib/zuul/.ssh/id_rsa.pub
Finally you need to activate the gerrit_connections setting in sfconfig.yaml:

.. code-block:: yaml

   gerrit_connections:
        - name: openstack_gerrit
          hostname: review.openstack.org
          puburl: https://review.openstack.org/r/
          username: third-party-ci-username

Running "sfconfig.sh" will apply the required change.

To benefit from Software Factory CI capabilities as a third party CI, you
also need to configure the config repository to enable a new gerrit trigger.
For example, to setup a basic check pipeline, add a new 'zuul/thirdparty.yaml'
file like this:

.. code-block:: yaml

    pipelines:
        - name: 3rd-party-check
          manager: IndependentPipelineManager
          source: openstack_gerrit
          trigger:
              openstack_gerrit:
                  - event: patchset-created


Notice the source and trigger are called 'openstack_gerrit' as set in the
gerrit_connection name, instead of the default 'gerrit' name.


How can I distribute service to new instance ?
..............................................

By default, sfconfig.sh will deploy and configure all service on
the install server (allinone). To use a distributed architecture,
new instances needs to be manually deployed using the sf image,
then root ssh access needs to be granted using the service_rsa.pub
key.

Example of arch file to offload elasticsearch service to a dedicated
host:

.. code-block:: yaml

  inventory:
    - name: elasticsearch
      ip: 192.168.0.3
      roles:
        - elasticsearch

Note that sfconfig.sh won't disable a service previously deployed.

How-to create channels in Mumble ?
..................................

You need to log-in as SuperUser using the super_user_password
from the sfconfig.yaml configuration. If no password was set,
then you need to read it's value using:

  awk '/super_user_password:/ { print $2 }' /etc/puppet/hiera/sf/sfconfig.yaml

Then you can follow this documentation to create channels and
set custom ACL:

  https://wiki.mumble.info/wiki/Murmurguide#Becoming_Administrator_and_Registering_a_User

How can I use the Gerrit REST API?
..................................

You can use the Gerrit REST API to enhance the functionality based on
your needs. There is an extensive documentation available online:

  https://gerrit-review.googlesource.com/Documentation/rest-api.html

To use the Gerrit REST API in Software Factory, you have to create an API
password first. To do so, click the lock button on the upper right corner of the
dashboard. A popup will show you a random password that you have to use to
access Gerrit.
Next, you need to use a different URL to access the Gerrit API. For example, if
you want to query the list of changes, you would normally execute a request like
this (as described in
https://gerrit-review.googlesource.com/Documentation/rest-api-changes.html#list-changes):

  GET /changes/?q=status:open+is:watched&n=2 HTTP/1.0

The full URL for Software Factory would look like this:

  http://sftests.com/api/changes/?q=status:open+is:watched&n=2

Please note the /api/ here. Authenticated requests (as described in the Gerrit
documentation) would simply use /api/a/ and the generated API password from
above.
You can find a full working example to automate some tasks (in this case deleting a specific branch
on a list of projects) in `tools/deletebranches.py`.
