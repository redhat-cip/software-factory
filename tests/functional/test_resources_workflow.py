#!/bin/env python
#
# Copyright (C) 2016 Red Hat
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import re
import time
import json
import config
import shutil
import requests

from subprocess import Popen

from utils import Base
from utils import set_private_key
from utils import GerritGitUtils
from utils import JenkinsUtils

from utils import create_random_str

from pysflib.sfgerrit import GerritUtils


class TestResourcesWorkflow(Base):

    def setUp(self):
        super(TestResourcesWorkflow, self).setUp()
        priv_key_path = set_private_key(
            config.USERS[config.ADMIN_USER]["privkey"])
        self.gitu_admin = GerritGitUtils(
            config.ADMIN_USER,
            priv_key_path,
            config.USERS[config.ADMIN_USER]['email'])
        self.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.ju = JenkinsUtils()

        self.dirs_to_delete = []

    def tearDown(self):
        super(TestResourcesWorkflow, self).tearDown()
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def ssh_run_cmd(self, sshkey_priv_path, user, host, subcmd):
        host = '%s@%s' % (user, host)
        sshcmd = ['ssh', '-o', 'LogLevel=ERROR',
                  '-o', 'StrictHostKeyChecking=no',
                  '-o', 'UserKnownHostsFile=/dev/null', '-i',
                  sshkey_priv_path, host]
        cmd = sshcmd + subcmd

        devnull = open(os.devnull, 'wb')
        p = Popen(cmd, stdout=devnull, stderr=devnull)
        return p.communicate(), p.returncode

    def clone_as_admin(self, pname):
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST,
                                        pname)
        clone_dir = self.gitu_admin.clone(url, pname)
        if os.path.dirname(clone_dir) not in self.dirs_to_delete:
            self.dirs_to_delete.append(os.path.dirname(clone_dir))
        return clone_dir

    def commit_direct_push_as_admin(self, clone_dir, msg):
        # Stage, commit and direct push the additions on master
        self.gitu_admin.add_commit_for_all_new_additions(clone_dir, msg)
        self.gitu_admin.direct_push_branch(clone_dir, 'master')

    def set_resources_then_direct_push(self, fpath,
                                       resources=None, mode='add'):
        config_clone_dir = self.clone_as_admin("config")
        path = os.path.join(config_clone_dir, fpath)
        if mode == 'add':
            file(path, 'w').write(resources)
        elif mode == 'del':
            os.unlink(path)
        last_success_build_num_cu = \
            self.ju.get_last_build_number("config-update",
                                          "lastSuccessfulBuild")
        self.commit_direct_push_as_admin(
            config_clone_dir,
            "Add new resources for functional tests")
        self.ju.wait_till_job_completes("config-update",
                                        last_success_build_num_cu,
                                        "lastSuccessfulBuild",
                                        max_retries=120)
        # Give more time to underlying services to create resources
        time.sleep(2)

    def wait_for_jenkins_note(self, change_id):
        attempt = 0
        while "jenkins" not in self.gu.get_reviewers(change_id):
            if attempt >= 90:
                break
            time.sleep(1)
            attempt += 1

    def propose_resources_change_check_ci(
            self, fpath, resources=None,
            mode='add', expected='failure'):

        config_clone_dir = self.clone_as_admin("config")
        path = os.path.join(config_clone_dir, fpath)
        if mode == 'add':
            file(path, 'w').write(resources)
        elif mode == 'del':
            os.unlink(path)

        if expected == 'success':
            label = "lastSuccessfulBuild"
            note = '+1'
        if expected == 'failure':
            label = "lastFailedBuild"
            note = '-1'

        last_build = self.ju.get_last_build_number("config-check",
                                                   label)

        self.gitu_admin.add_commit_and_publish(
            config_clone_dir, "master", "Validate resources",
            fnames=[path])

        change_ids = self.gu.get_my_changes_for_project('config')
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]

        self.ju.wait_till_job_completes("config-check",
                                        last_build,
                                        label,
                                        max_retries=120)
        self.wait_for_jenkins_note(change_id)
        self.assertEqual(
            self.gu.get_reviewer_approvals(change_id, 'jenkins')['Verified'],
            note)

    def get_resources(self):
        gateau = config.USERS[config.ADMIN_USER]['auth_cookie']
        resp = requests.get("%s/manage/resources/" % config.GATEWAY_URL,
                            cookies={'auth_pubtkt': gateau})
        return resp.json()

    def test_validate_wrong_resource_workflow(self):
        """ Check resources - wrong model is detected by config-check """
        # This resource is not correct
        fpath = "resources/%s.yaml" % create_random_str()
        name = create_random_str()
        resources = """resources:
  groups:
    %s:
      description: test for functional test
"""
        # Add the resource file with review then check CI
        resources = resources % name
        self.propose_resources_change_check_ci(fpath,
                                               resources=resources,
                                               mode='add',
                                               expected='failure')

    def test_validate_correct_resource_workflow(self):
        """ Check resources - good model is detected by config-check """
        # This resource is correct
        fpath = "resources/%s.yaml" % create_random_str()
        name = create_random_str()
        resources = """resources:
  groups:
    %s:
      name: %s
      description: test for functional test
      members:
        - user2@sftests.com
"""
        # Add the resource file with review then check CI
        resources = resources % (name, name)
        self.propose_resources_change_check_ci(fpath,
                                               resources=resources,
                                               mode='add',
                                               expected='success')

    def test_CUD_group(self):
        """ Check resources - ops on group work as expected """
        fpath = "resources/%s.yaml" % create_random_str()
        name = create_random_str()
        resources = """resources:
  groups:
    %s:
      name: %s
      description: test for functional test
      members:
        - user2@sftests.com
        - user3@sftests.com
"""
        # Add the resources file w/o review
        resources = resources % (name, name)
        self.set_resources_then_direct_push(fpath,
                                            resources=resources,
                                            mode='add')
        # Check members on Gerrit
        gid = self.gu.get_group_id(name)
        members = [m['email'] for m in self.gu.get_group_members(gid)]
        self.assertIn("user2@sftests.com", members)
        self.assertIn("user3@sftests.com", members)
        # Modify resources Add/Remove members w/o review
        resources = """resources:
  groups:
    %s:
      name: %s
      description: test for functional test
      members:
        - user4@sftests.com
        - user2@sftests.com
"""
        resources = resources % (name, name)
        self.set_resources_then_direct_push(fpath,
                                            resources=resources,
                                            mode='add')
        # Check members on Gerrit
        gid = self.gu.get_group_id(name)
        members = [m['email'] for m in self.gu.get_group_members(gid)]
        self.assertIn("user4@sftests.com", members)
        self.assertIn("user2@sftests.com", members)
        self.assertNotIn("user3@sftests.com", members)
        # Del the resources file w/o review
        self.set_resources_then_direct_push(fpath,
                                            mode='del')
        # Check the group has been deleted
        self.assertFalse(
            self.gu.get_group_id(name))

    def test_CD_repo(self):
        """ Check resources - ops on git repositories work as expected """
        fpath = "resources/%s.yaml" % create_random_str()
        name = create_random_str()
        resources = """resources:
  repos:
    %s:
      name: %s
      description: test for functional test
"""
        # Add the resources file w/o review
        resources = resources % (name, name)
        self.set_resources_then_direct_push(fpath,
                                            resources=resources,
                                            mode='add')
        # Check the project has been created
        self.assertTrue(self.gu.project_exists(name))
        # Del the resources file w/o review
        self.set_resources_then_direct_push(fpath,
                                            mode='del')
        # Check the project has been deleted
        self.assertFalse(self.gu.project_exists(name))

    def test_CRUD_resources(self):
        """ Check resources - bulk ops on resources work as expected """
        fpath = "resources/%s.yaml" % create_random_str()
        tmpl_keys = {'pname': create_random_str(),
                     'r1name': create_random_str(),
                     'r2name': create_random_str(),
                     'aname': create_random_str(),
                     'g1name': create_random_str(),
                     'g2name': create_random_str()}
        resources = """resources:
  projects:
    %(pname)s:
      name: %(pname)s
      description: An awesome project
      contacts:
        - contact@grostest.com
      source-repositories:
        - %(r1name)s
        - %(r2name)s
      website: http://ichiban-cloud.io
      documentation: http://ichiban-cloud.io/docs
      issue-tracker: http://ichiban-cloud.bugtrackers.io
  repos:
    %(r1name)s:
      name: %(pname)s/%(r1name)s
      description: The server part
      acl: %(aname)s
    %(r2name)s:
      name: %(pname)s/%(r2name)s
      description: The client part
      acl: %(aname)s
  acls:
    %(aname)s:
      file: |
        [access "refs/*"]
          read = group Anonymous Users
          read = group %(pname)s/%(g2name)s
          owner = group %(pname)s/%(g1name)s
        [access "refs/heads/*"]
          label-Code-Review = -2..+2 group %(pname)s/%(g2name)s
          label-Verified = -2..+2 group %(pname)s/%(g1name)s
          label-Workflow = -1..+1 group %(pname)s/%(g2name)s
          submit = group %(pname)s/%(g2name)s
          read = group Anonymous Users
          read = group %(pname)s/%(g2name)s
        [access "refs/meta/config"]
          read = group %(pname)s/%(g2name)s
        [receive]
          requireChangeId = true
        [submit]
          mergeContent = false
          action = fast forward only
      groups:
        - %(g1name)s
        - %(g2name)s
  groups:
    %(g1name)s:
      name: %(pname)s/%(g1name)s
      members:
        - user2@sftests.com
    %(g2name)s:
      name: %(pname)s/%(g2name)s
      members:
        - user3@sftests.com
        - user4@sftests.com
"""
        # Add the resources file w/o review
        resources = resources % tmpl_keys
        self.set_resources_then_direct_push(fpath,
                                            resources=resources,
                                            mode='add')
        # Check resources have been created
        self.assertTrue(self.gu.project_exists(
                        os.path.join(tmpl_keys['pname'],
                                     tmpl_keys['r1name'])))
        self.assertTrue(self.gu.project_exists(
                        os.path.join(tmpl_keys['pname'],
                                     tmpl_keys['r2name'])))
        gid = self.gu.get_group_id(os.path.join(tmpl_keys['pname'],
                                                tmpl_keys['g1name']))
        members = [m['email'] for m in self.gu.get_group_members(gid)]
        self.assertEqual(len(members), 1)
        self.assertIn("user2@sftests.com", members)
        gid2 = self.gu.get_group_id(os.path.join(tmpl_keys['pname'],
                                                 tmpl_keys['g2name']))
        members = [m['email'] for m in self.gu.get_group_members(gid2)]
        self.assertEqual(len(members), 2)
        self.assertIn("user3@sftests.com", members)
        self.assertIn("user4@sftests.com", members)
        # Verify ACLs have been written for both repo
        for r in ('r1name', 'r2name'):
            rname = os.path.join(tmpl_keys['pname'], tmpl_keys[r])
            acl = self.gu.g.get('access/?project=%s' % rname)
            self.assertIn(
                gid2,
                acl[rname]['local']['refs/heads/*']
                   ['permissions']['submit']['rules'].keys())
        # Verify the resources endpoint know about what we pushed
        res = self.get_resources()
        self.assertIn(tmpl_keys['pname'],
                      res['resources']['projects'].keys())
        self.assertIn(tmpl_keys['aname'],
                      res['resources']['acls'].keys())
        self.assertIn(tmpl_keys['g1name'],
                      res['resources']['groups'].keys())
        self.assertIn(tmpl_keys['g2name'],
                      res['resources']['groups'].keys())
        self.assertIn(tmpl_keys['r1name'],
                      res['resources']['repos'].keys())
        self.assertIn(tmpl_keys['r2name'],
                      res['resources']['repos'].keys())
        # Modify the ACL to verify repos ACL are updated
        resources = re.sub('submit = group .*',
                           'submit = group %s' % os.path.join(
                               tmpl_keys['pname'], tmpl_keys['g1name']),
                           resources)
        self.set_resources_then_direct_push(fpath,
                                            resources=resources,
                                            mode='add')
        # Verify ACLs have been updated for both repo
        for r in ('r1name', 'r2name'):
            rname = os.path.join(tmpl_keys['pname'], tmpl_keys[r])
            acl = self.gu.g.get('access/?project=%s' % rname)
            self.assertIn(
                gid,
                acl[rname]['local']['refs/heads/*']
                          ['permissions']['submit']['rules'].keys())
        # Now let's remove all that awesome resources
        self.set_resources_then_direct_push(fpath,
                                            mode='del')
        # Check resources have been deleted
        self.assertFalse(self.gu.project_exists(
                         os.path.join(tmpl_keys['pname'],
                                      tmpl_keys['r1name'])))
        self.assertFalse(self.gu.project_exists(
                         os.path.join(tmpl_keys['pname'],
                                      tmpl_keys['r2name'])))
        self.assertFalse(self.gu.get_group_id(
            os.path.join(tmpl_keys['pname'],
                         tmpl_keys['g1name'])))
        self.assertFalse(self.gu.get_group_id(
            os.path.join(tmpl_keys['pname'],
                         tmpl_keys['g2name'])))
        res = self.get_resources()
        projects = res['resources'].get('projects', {})
        acls = res['resources'].get('acls', {})
        groups = res['resources'].get('groups', {})
        repos = res['resources'].get('repos', {})
        self.assertNotIn(tmpl_keys['pname'], projects.keys())
        self.assertNotIn(tmpl_keys['aname'], acls.keys())
        self.assertNotIn(tmpl_keys['g1name'], groups.keys())
        self.assertNotIn(tmpl_keys['g2name'], groups.keys())
        self.assertNotIn(tmpl_keys['r1name'], repos.keys())
        self.assertNotIn(tmpl_keys['r2name'], repos.keys())

    def test_GET_resources(self):
        """ Check resources - GET resources works as expected"""
        cookies = dict(auth_pubtkt=config.USERS[config.USER_1]['auth_cookie'])
        ret = requests.get("%s/manage/resources/" % config.GATEWAY_URL,
                           cookies=cookies)
        self.assertIn('resources', ret.json())

    def test_GET_missing_resources(self):
        """ Check resources - GET missing resources works as expected"""
        token = config.USERS[config.ADMIN_USER]['auth_cookie']
        prev = "resources: {}"
        new = """resources:
  groups:
    %(gname)s:
      name: %(gname)s
      description: A test group
      members: ['user2@sftests.com']
"""
        group_name = create_random_str()
        data = {'prev': prev, 'new': new % {'gname': group_name}}
        # Direct PUT resources bypassing the config repo workflow
        requests.put("%s/manage/resources/" % config.GATEWAY_URL,
                     json=data,
                     cookies={'auth_pubtkt': token})
        # Verify managesf detects diff and propose a re-sync resource struct
        ret = requests.get("%s/manage/resources/?get_missing_"
                           "resources=true" % config.GATEWAY_URL,
                           cookies={'auth_pubtkt': token})
        logs, resources = ret.json()
        self.assertListEqual(logs, [])
        self.assertIn(group_name, resources['resources']['groups'])
        # Call the resources.sh script on managesf node to propose
        # a review on the config repo to re-sync with the reality
        cmd = ['/usr/local/bin/resources.sh',
               'get_missing_resources', 'submit']
        self.ssh_run_cmd(config.SERVICE_PRIV_KEY_PATH,
                         'root',
                         config.GATEWAY_HOST, cmd)
        # Get change id of the submitted review
        search_string = "Propose missing resources to the config repo"
        r = requests.get(
            '%s/r/changes/?q=%s' % (config.GATEWAY_URL, search_string))
        lastid = 0
        for r in json.loads(r.content[4:]):
            if r['_number'] > lastid:
                lastid = r['_number']
        change_id = str(lastid)
        # Check Jenkins reported Verified +1 on that change
        self.wait_for_jenkins_note(change_id)
        while True:
            time.sleep(1)
            ret = self.gu.get_reviewer_approvals(
                change_id, 'jenkins')['Verified']
            if int(ret) != 0:
                break
        self.assertEqual(
            self.gu.get_reviewer_approvals(
                change_id, 'jenkins')['Verified'], '+1')
        # Check flag "sf-resources: skip-apply" in the commit msg
        changes = self.gu.g.get('changes/')
        change = [c for c in changes if c["_number"] == int(change_id)][0]
        self.assertEqual(change['subject'],
                         'Propose missing resources to the config repo')
        cmt = self.gu.g.get('changes/%s/'
                            'revisions/current/commit' % change['id'])
        self.assertTrue(cmt['message'].find('sf-resources: skip-apply') > 0)
        # Fetch the last successful build ID for the config-update job
        last_success_build_num_cu = \
            self.ju.get_last_build_number("config-update",
                                          "lastSuccessfulBuild")
        # Approve the change and wait for the +2
        self.gu.submit_change_note(change['id'], "current", "Code-Review", "2")
        self.gu.submit_change_note(change['id'], "current", "Workflow", "1")
        self.wait_for_jenkins_note(change_id)
        while True:
            time.sleep(1)
            ret = self.gu.get_reviewer_approvals(
                change_id, 'jenkins')['Verified']
            if int(ret) != 0 and int(ret) != -1 and int(ret) != +1:
                break
        self.assertEqual(
            self.gu.get_reviewer_approvals(
                change_id, 'jenkins')['Verified'], '+2')
        # Check config-update return a success
        # The flag sf-resources: skip-apply should be detected
        # by the config update. Then missing resources won't
        # by concidered new and the resources apply will be skipped.
        # This tests (checking config-update succeed) confirm
        # resource apply have been skipped if not managesf resources
        # apply would have return 409 error making config-update failed too.
        self.ju.wait_till_job_completes("config-update",
                                        last_success_build_num_cu,
                                        "lastSuccessfulBuild",
                                        max_retries=120)
        previous = last_success_build_num_cu
        last_success_build_num_cu = \
            self.ju.get_last_build_number("config-update",
                                          "lastSuccessfulBuild")
        # If not True then we cannot concider config-update succeed
        self.assertEqual(previous + 1, last_success_build_num_cu)
        # Checking again missing resources  must return nothing
        ret = requests.get("%s/manage/resources/?get_missing_"
                           "resources=true" % config.GATEWAY_URL,
                           cookies={'auth_pubtkt': token})
        logs, resources = ret.json()
        self.assertListEqual(logs, [])
        self.assertEqual(len(resources['resources']), 0)
