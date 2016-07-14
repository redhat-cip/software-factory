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


Why can't I +2 after being added to the core group ?
....................................................

This may happen because of web browser cache issues. Remove all
cookies and logout/login to refresh your gerrit privileges.


Why my job fails with the "NOT_REGISTERED" error ?
..................................................

This error happens when zuul can't run a job. Most of the time it's because:

* A project gate is configured with an unknown job. Jobs definition
  are likely missing the job used in zuul layout.
* A slave node label has never been ready. Zuul fails with NOT_REGISTERED
  (instead of queuing) until a first slave with the correct node label is available.
  Then after, once Zuul knows a label really exists, it will properly queue jobs.

The first step to investigate that error is to verify the job is active
in jenkins dashboard. If the job is not there, check the config-repo and check
if the job is either expanded from a job-template (using project name), or
either the project is fully defined. Otherwise add the job and update
the config repo.


Why my job stays in "queued" ?
..............................

This happens when no slaves are available to execute a job:

* First check that slaves are attached to jenkins using the dashboard
  (slaves are shown in the left column)
* Then verify node labels are corresponding between slave and jjb definition.


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


How-to setup swift mirror of external requirements ?
....................................................

The mirror service uses the mirror2swift utility to provide a local cache
for external ressources. It's usualy used to mirror rpm repository
for ci image building purpose.

To enable the mirror service, you need to configure a swift container
in sfconfig.yaml and then specify what url needs to be mirrored in the config-repo:

* Add the mirror role to /etc/puppet/hiera/sf/arch.yaml
* Configure the mirror role in /etc/puppet/hiera/sf/sfconfig.yaml
* Run sfconfig.sh
* Edit mirror configuration template provided in config repo mirrors directory.

When the periodic_update is set, the mirror update will be sceduled periodically
through a dedicated zuul pipeline, status and progress can be checked like any
other CI jobs. Otherwise, to update the cache manually, this command needs to be
executed:

.. code-block:: bash

    sudo -u mirror2swift mirror2swift /var/lib/mirror2swift/config.yaml


sfconfig.yaml example:

.. code-block:: yaml

  mirrors:
    periodic_update: '0 0 * * \*'
    swift_mirror_url: http://swift:8080/v1/AUTH_uuid/repomirror/
    swift_mirror_tempurl_key: TEMP_URL_KEY

The swift_mirror_url needs to be the canonical fully qualified url of the destination swift container.
The swift_mirror_tempurl_key needs to be a write access tempurl key.
The periodic_update needs to be a valid zuul timer format, e.g. daily is '0 0 * * \*'.

config-repo yaml files represent the list of mirrors as documented here
https://github.com/cschwede/mirror2swift. For example, config/mirrors/centos.yaml:

.. code-block:: yaml

  - name: os
    type: repodata
    url: 'http://centos.mirror.example.com/7/os/x86_64/'
    prefix: 'os/'

This will mirror the CentOS-7 base repository to http://swift:8080/v1/AUTH_uuid/repomirror/os/


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
