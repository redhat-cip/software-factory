#!/usr/bin/python
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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
import shutil
import time

import requests

import config
from utils import Base
from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import create_random_str

from pysflib.sfgerrit import GerritUtils


class TestGerrit(Base):
    """ Functional tests that validate some gerrit behaviors.
    """
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.clone_dirs = []
        self.dirs_to_delete = []
        self.msu = ManageSfUtils(config.GATEWAY_URL)

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def create_project(self, name, options=None):
        self.msu.createProject(name,
                               config.ADMIN_USER,
                               options=options)
        self.projects.append(name)

    def test_review_labels(self):
        """ Test if list of review labels are as expected
        """
        pname = 'p_%s' % create_random_str()
        self.create_project(pname)
        un = config.ADMIN_USER
        gu = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[un]['auth_cookie'])
        k_index = gu.add_pubkey(config.USERS[un]["pubkey"])
        self.assertTrue(gu.project_exists(pname))
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s:29418/%s" % (un, config.GATEWAY_HOST,
                                        pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")

        change_ids = gu.get_my_changes_for_project(pname)
        self.assertEqual(len(change_ids), 1)
        change_id = change_ids[0]

        labels = gu.get_labels_list_for_change(change_id)

        self.assertIn('Workflow', labels)
        self.assertIn('Code-Review', labels)
        self.assertIn('Verified', labels)
        self.assertEqual(len(labels.keys()), 3)

        gu.del_pubkey(k_index)

    def _prepare_review_submit_testing(self, project_options=None):
        if project_options is None:
            u2mail = config.USERS[config.USER_2]['email']
            project_options = {'core-group': u2mail}
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, project_options)
        un = config.ADMIN_USER
        gu = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[un]['auth_cookie'])
        k_index = gu.add_pubkey(config.USERS[un]["pubkey"])
        self.assertTrue(gu.project_exists(pname))
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s:29418/%s" % (un, config.GATEWAY_HOST,
                                        pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")

        change_ids = gu.get_my_changes_for_project(pname)
        self.assertEqual(len(change_ids), 1)
        change_id = change_ids[0]

        return change_id, gu, k_index

    def test_review_submit_approval(self):
        """ Test submit criteria - CR(2 +2s), V(+1), A(+1)
        """
        change_id, gu, k_index = self._prepare_review_submit_testing()

        gu.submit_change_note(change_id, "current", "Code-Review", "1")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu.submit_change_note(change_id, "current", "Verified", "2")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu.submit_change_note(change_id, "current", "Workflow", "1")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu.submit_change_note(change_id, "current", "Code-Review", "2")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu_user2 = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[config.USER_2]['auth_cookie'])
        gu_user2.submit_change_note(change_id, "current", "Code-Review", "2")
        self.assertTrue(gu.submit_patch(change_id, "current"))
        gu.del_pubkey(k_index)

    def test_review_submit_approval_with_extra_code_review(self):
        """ Test submit criteria - CR(3 +2s), V(+1), A(+1)
        """
        u2mail = config.USERS[config.USER_2]['email']
        u3mail = config.USERS[config.USER_3]['email']
        options = {'core-group': '%s,%s' % (u2mail, u3mail)}
        change_id, gu, k_index = self._prepare_review_submit_testing(options)

        gu.submit_change_note(change_id, "current", "Code-Review", "1")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu.submit_change_note(change_id, "current", "Verified", "2")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu.submit_change_note(change_id, "current", "Workflow", "1")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu.submit_change_note(change_id, "current", "Code-Review", "2")
        self.assertFalse(gu.submit_patch(change_id, "current"))

        gu_user2 = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[config.USER_2]['auth_cookie'])
        gu_user2.submit_change_note(change_id, "current", "Code-Review", "2")
        gu_user3 = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[config.USER_3]['auth_cookie'])
        gu_user3.submit_change_note(change_id, "current", "Code-Review", "2")

        self.assertTrue(gu.submit_patch(change_id, "current"))
        gu.del_pubkey(k_index)

    def test_plugins_installed(self):
        """ Test if plugins are present
        """
        gu = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        plugins = gu.list_plugins()
        self.assertIn('download-commands', plugins)
        self.assertIn('gravatar-avatar-provider', plugins)
        self.assertIn('reviewers-by-blame', plugins)

    def test_check_download_commands(self):
        """ Test if download commands plugin works
        """
        pname = 'p_%s' % create_random_str()
        self.create_project(pname)
        un = config.ADMIN_USER
        gu = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[un]['auth_cookie'])
        self.assertTrue(gu.project_exists(pname))
        k_index = gu.add_pubkey(config.USERS[un]["pubkey"])
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s:29418/%s" % (un, config.GATEWAY_HOST,
                                        pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")

        change_ids = gu.get_my_changes_for_project(pname)
        self.assertEqual(len(change_ids), 1)
        change_id = change_ids[0]
        resp = gu.get_change_last_patchset(change_id)
        self.assertIn("current_revision", resp)
        self.assertIn("revisions", resp)
        current_rev = resp["current_revision"]
        fetch = resp["revisions"][current_rev]["fetch"]
        self.assertGreater(fetch.keys(), 0)

        # disable and check if the fetch has anything
        gu.e_d_plugin("download-commands", 'disable')
        resp = gu.get_change_last_patchset(change_id)
        fetch = resp["revisions"][current_rev]["fetch"]
        self.assertEqual(len(fetch.keys()), 0)

        # enable the plugin and check if the fetch information is valid
        gu.e_d_plugin("download-commands", 'enable')
        resp = gu.get_change_last_patchset(change_id)
        fetch = resp["revisions"][current_rev]["fetch"]
        self.assertGreater(len(fetch.keys()), 0)

        gu.del_pubkey(k_index)

    def test_check_add_automatic_reviewers(self):
        """ Test if reviewers-by-blame plugin works
        """
        pname = 'p_%s' % create_random_str()
        u2mail = config.USERS[config.USER_2]['email']
        options = {'core-group': u2mail}
        self.create_project(pname, options)
        first_u = config.ADMIN_USER
        gu_first_u = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[first_u]['auth_cookie'])
        self.assertTrue(gu_first_u.project_exists(pname))
        # Push data in the create project as Admin user
        k1_index = gu_first_u.add_pubkey(config.USERS[first_u]["pubkey"])
        priv_key_path = set_private_key(config.USERS[first_u]["privkey"])
        gitu = GerritGitUtils(first_u,
                              priv_key_path,
                              config.USERS[first_u]['email'])
        url = "ssh://%s@%s:29418/%s" % (first_u, config.GATEWAY_HOST,
                                        pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        data = ['this', 'is', 'a', 'couple', 'of', 'lines']
        clone_dir = gitu.clone(url, pname)
        file(os.path.join(clone_dir, "file"), 'w').write("\n".join(data))
        gitu.add_commit_and_publish(clone_dir, "master", "Test commit",
                                    fnames=["file"])
        # Get the change id
        change_ids = gu_first_u.get_my_changes_for_project(pname)
        self.assertEqual(len(change_ids), 1)
        change_id = change_ids[0]
        # Merge the change
        gu_first_u.submit_change_note(change_id, "current", "Code-Review", "2")
        gu_first_u.submit_change_note(change_id, "current", "Verified", "2")
        gu_first_u.submit_change_note(change_id, "current", "Workflow", "1")
        second_u = config.USER_2
        gu_second_u = GerritUtils(
            'https://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[second_u]['auth_cookie'])
        gu_second_u.submit_change_note(
            change_id, "current", "Code-Review", "2")
        self.assertTrue(gu_first_u.submit_patch(change_id, "current"))
        # Change the file we have commited with Admin user
        k2_index = gu_second_u.add_pubkey(config.USERS[second_u]["pubkey"])
        priv_key_path = set_private_key(config.USERS[second_u]["privkey"])
        gitu = GerritGitUtils(second_u,
                              priv_key_path,
                              config.USERS[second_u]['email'])
        url = "ssh://%s@%s:29418/%s" % (second_u, config.GATEWAY_HOST,
                                        pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        data = ['this', 'is', 'some', 'lines']
        file(os.path.join(clone_dir, "file"), 'w').write("\n".join(data))
        gitu.add_commit_and_publish(clone_dir, "master", "Test commit",
                                    fnames=["file"])
        # Get the change id
        change_ids = gu_second_u.get_my_changes_for_project(pname)
        self.assertEqual(len(change_ids), 1)
        change_id = change_ids[0]
        # Verify first_u has been automatically added to reviewers
        attempts = 0
        while True:
            if len(gu_second_u.get_reviewers(change_id)) > 0 or attempts >= 3:
                break
            attempts += 1
            time.sleep(1)
        reviewers = gu_second_u.get_reviewers(change_id)
        self.assertEqual(len(reviewers), 1)
        self.assertEqual(reviewers[0], first_u)

        gu_first_u.del_pubkey(k1_index)
        gu_second_u.del_pubkey(k2_index)

    def test_gerrit_version(self):
        """ Test if correct Gerrit version is running
        """
        url = "https://%s/r/config/server/version" % config.GATEWAY_HOST
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertTrue('"2.8.6.1-dirty"' in resp.text)
