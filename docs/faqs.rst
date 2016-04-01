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
A full example to automate some tasks (in this case deleting a specific branch
on a list of projects) is given below.

.. code-block:: python

  #!/usr/bin/env python
  import argparse
  import json
  import requests
  import sys


  def status(ok, last=False):
      if ok:
          sys.stdout.write('+')
      else:
          sys.stdout.write('-')
      if last:
          print ""


  def main():
      parser = argparse.ArgumentParser(description='Delete branches')
      parser.add_argument('-u', '--user', type=str, required=True,
                          help='Gerrit username')
      parser.add_argument('-p', '--password', type=str, required=True,
                          help='Gerrit HTTP password')
      parser.add_argument('-b', '--branch', type=str, required=True,
                          help='Branch to delete')
      parser.add_argument('-d', '--default-branch', type=str, required=False,
                          help='New default branch')
      parser.add_argument('-f', '--filter', type=str, required=True,
                          help='Projectname filter, for example "-distgit"')
      parser.add_argument('--host', type=str, required=True,
                          help='Gerrit host, for example sftests.com')
      parser.add_argument('-n', '--no-op', action='store_true', required=False,
                          help='Do not delete repos, only print actions')

      args = parser.parse_args()

      if args.branch == "master" and not args.default_branch:
          raise parser.error(
              "Need a new default branch if master will be deleted")

      url = "http://%s:%s@%s/api/a/projects/" % (
          args.user, args.password, args.host)
      resp = requests.get(url)
      projects = json.loads(resp.content[4:])

      for project_name in projects.keys():
          if project_name.endswith(args.filter):
              if not args.no_op:
                  print "Deleting branch %s on project %s: " % (
                      args.branch, project_name),

                  if args.default_branch:
                      headers = {'Authorization': 'token %s' % args.token,
                                 'Content-Type': 'application/json'}
                      data = json.dumps({"ref": "refs/heads/%s" % args.default_branch })
                      gerrit_url = "http://%s:%s@%s/api/a/projects/%s/HEAD" % (
                          args.user, args.password, args.host, project_name)
                      resp = requests.put(gerrit_url, headers=headers, data=data)
                      status(resp.ok)

                  headers = {'Authorization': 'token %s' % args.token}
                  gerrit_url = "http://%s:%s@%s/api/a/projects/%s/branches/%s" % (
                      args.user, args.password, args.host, project_name, args.branch)
                  resp = requests.delete(gerrit_url, headers=headers)
                  status(resp.ok)
              else:
                  print "Would delete branch %s on project %s" % (
                      args.branch, project_name)


  if __name__ == '__main__':
      main()
