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
import config
import yaml
import shutil
import time

from utils import Base
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import create_random_str
from utils import set_private_key
from utils import GerritUtil
from utils import RedmineUtil


class TestGerritHooks(Base):
    """ Functional tests that validate Gerrit hooks.
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.MANAGESF_HOST, 80)
        # TODO(fbo): Sould be fetch from the config
        # Fix it in test_01 too.
        with open(os.environ['SF_ROOT'] + "/build/hiera/redmine.yaml") as f:
            ry = yaml.load(f)
        cls.redmine_api_key = ry['redmine']['issues_tracker_api_key']

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []
        self.issues = []
        self.u = config.ADMIN_USER
        self.u2 = config.USER_2
        self.rm = RedmineUtil(config.REDMINE_SERVER,
                              apiKey=self.redmine_api_key)
        self.gu = GerritUtil(config.GERRIT_SERVER,
                             username=self.u)
        self.gu2 = GerritUtil(config.GERRIT_SERVER,
                              username=self.u2)
        self.gu.addPubKey(config.USERS[self.u]["pubkey"])
        priv_key_path = set_private_key(config.USERS[self.u]["privkey"])
        self.gitu = GerritGitUtils(self.u,
                                   priv_key_path,
                                   config.USERS[self.u]['email'])

    def tearDown(self):
        for issue in self.issues:
            self.rm.deleteIssue(issue)
        for name in self.projects:
            self.msu.deleteProject(name, self.u)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def createProject(self, name, user,
                      options=None):
        self.msu.createProject(name, user,
                               options)
        self.projects.append(name)

    def test_update_issue_hooks(self):
        """ A referenced issue in commit msg triggers the hook
        """
        pname = 'p_%s' % create_random_str()

        # Be sure the project does not exist
        self.msu.deleteProject(pname, self.u)

        # Create the project
        self.createProject(pname, self.u)
        # Put USER_2 as core for the project
        self.gu.addGroupMember(self.u2, "%s-core" % pname)

        # Create an issue on the project
        issue_id = self.rm.createIssue(pname, "There is a problem")

        # Clone and commit something
        url = "ssh://%s@%s/%s" % (self.u, config.GERRIT_HOST,
                                  pname)
        clone_dir = self.gitu.clone(url, pname)
        cmt_msg = "Fix bug: %s" % issue_id
        self.gitu.add_commit_and_publish(clone_dir, 'master', cmt_msg)

        # Check issue status (Gerrit hook updates the issue to in progress)
        time.sleep(3)
        self.assertTrue(self.rm.isIssueInProgress(issue_id))

        # Get the change id and merge the patch
        change_ids = self.gu.getMyChangesForProject(pname)
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]
        self.gu.setPlus2CodeReview(change_id, "current")
        self.gu.setPlus1Approved(change_id, "current")
        self.gu.setPlus1Verified(change_id, "current")
        self.gu2.setPlus2CodeReview(change_id, "current")
        self.assertEqual(
            self.gu.submitPatch(change_id, "current")['status'], 'MERGED')

        # Check issue status (Gerrit hook updates the issue to in progress)
        time.sleep(3)
        self.assertTrue(self.rm.isIssueClosed(issue_id))
