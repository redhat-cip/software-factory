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
import shutil
import time
import requests as http

from utils import Base
from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import GerritUtil
from utils import JenkinsUtils


class TestZuulOps(Base):
    """ Functional tests to validate config repo bootstrap
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_HOST, 80)
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def createProject(self, name, user,
                      options=None):
        self.msu.createProject(name, user,
                               options)
        self.projects.append(name)


    def test_check_zuul_operations(self):
        """ Test if zuul verifies project correctly through zuul-demo project
        """
        # zuul-demo - test project used exclusively to test zuul installation
        # The necessary project descriptions are already declared in Jenkins
        # and zuul
        pname = 'zuul-demo'
        self.createProject(pname, config.ADMIN_USER)

        # Clone the project and submit it for review
        un = config.ADMIN_USER
        gu = GerritUtil(config.GERRIT_SERVER, username=un)
        ju = JenkinsUtils()
        k_index = gu.addPubKey(config.USERS[un]["pubkey"])
        # Gerrit part
        assert gu.isPrjExist(pname)
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s/%s" % (un, config.GERRIT_HOST,
                                  pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        last_fail_build_num_ft = \
            ju.get_last_build_number("zuul-demo-functional-tests",
                                     "lastFailedBuild")
        last_fail_build_num_ut = \
            ju.get_last_build_number("zuul-demo-unit-tests",
                                      "lastFailedBuild")
        last_succeed_build_num_ft = \
            ju.get_last_build_number("zuul-demo-functional-tests",
                                     "lastSuccessfulBuild")
        last_succeed_build_num_ut = \
            ju.get_last_build_number("zuul-demo-unit-tests",
                                     "lastSuccessfulBuild")

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")

        change_ids = gu.getMyChangesForProject(pname)
        self.assertEqual(len(change_ids), 1)
        change_id = change_ids[0]

        # Give some time for jenkins to work
        ju.wait_till_job_completes("zuul-demo-functional-tests",
                                   last_fail_build_num_ft, "lastFailedBuild")
        ju.wait_till_job_completes("zuul-demo-unit-tests",
                                   last_fail_build_num_ut, "lastFailedBuild")

        attempt = 0
        while not "jenkins" in gu.getReviewers(change_id):
            if attempt >= 10:
                break
            time.sleep(1)
            attempt += 1

        attempt = 0
        while gu.getReviewerApprovals(change_id, 'jenkins')['Verified'] != '-1':
            if attempt >= 30:
                break
            time.sleep(1)
            attempt += 1

        self.assertEqual(
            gu.getReviewerApprovals(change_id, 'jenkins')['Verified'], '-1')

        # Add the test case files and resubmit for review
        data = "echo Working"
        files = ["run_functional-tests.sh", "run_tests.sh"]

        for f in files:
            file(os.path.join(clone_dir, f), 'w').write(data)
            os.chmod(os.path.join(clone_dir, f), 0755)

        gitu.add_commit_and_publish(clone_dir, "master", None, fnames=files)

        # Give some time for jenkins to work
        ju.wait_till_job_completes("zuul-demo-functional-tests",
                                   last_succeed_build_num_ft,
                                     "lastSuccessfulBuild")
        ju.wait_till_job_completes("zuul-demo-unit-tests",
                                   last_succeed_build_num_ut,
                                   "lastSuccessfulBuild")

        attempt = 0
        while not "jenkins" in gu.getReviewers(change_id):
            if attempt >= 30:
                break
            time.sleep(1)
            attempt += 1

        attempt = 0
        while gu.getReviewerApprovals(change_id, 'jenkins')['Verified'] != '+1':
            if attempt >= 30:
                break
            time.sleep(1)
            attempt += 1

        self.assertEqual(
            gu.getReviewerApprovals(change_id, 'jenkins')['Verified'], '+1')

        gu.delPubKey(k_index)
