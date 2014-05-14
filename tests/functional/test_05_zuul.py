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


class TestZuulOps(Base):
    """ Functional tests to validate config repo bootstrap
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.MANAGESF_HOST, 80)
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

    def get_last_build_number(self, job_name):
        url = config.JENKINS_SERVER
        url += "/job/%(job_name)s/lastBuild/buildNumber" \
               % {'job_name': job_name}
        try:
            resp = http.get(url)
            return int(resp.text)
        except:
            return 0

    def wait_till_job_completes(self, job_name, cur_build):
        retries = 0
        while True:
            url = config.JENKINS_SERVER
            url += "/job/%(job_name)s/lastFailedBuild/buildNumber" \
                   % {'job_name': job_name}
            try:
                resp = http.get(url)
                lfb = int(resp.text)
            except Exception:
                lfb = 0

            url = config.JENKINS_SERVER
            url += "/job/%(job_name)s/lastSuccessfulBuild/buildNumber" \
                   % {'job_name': job_name}
            try:
                resp = http.get(url)
                lsb = int(resp.text)
            except Exception:
                lsb = 0
            retries += 1

            if lsb > cur_build or lfb > cur_build or retries > 10:
                break
            else:
                time.sleep(1)

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

        current_build_num = \
            self.get_last_build_number("zuul-demo-functional-tests")
        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")

        change_ids = gu.getMyChangesForProject(pname)
        self.assertEqual(len(change_ids), 1)
        change_id = change_ids[0]

        # Give some time for jenkins to work
        self.wait_till_job_completes("zuul-demo-functional-tests",
                                     current_build_num)
        self.wait_till_job_completes("zuul-demo-unit-tests",
                                     current_build_num)

        reviewers = gu.getReviewers(change_id)
        assert 'jenkins' in reviewers

        approvals = gu.getReviewerApprovals(change_id, 'jenkins')
        assert approvals['Verified'] == '-1'

        # Add the test case files and resubmit for review
        data = "echo Working"
        files = ["run_functional-tests.sh", "run_tests.sh"]

        for f in files:
            file(os.path.join(clone_dir, f), 'w').write(data)
            os.chmod(os.path.join(clone_dir, f), 0755)

        current_build_num = \
            self.get_last_build_number("zuul-demo-functional-tests")
        gitu.add_commit_and_publish(clone_dir, "master", None, fnames=files)

        # Give some time for jenkins to work
        self.wait_till_job_completes("zuul-demo-functional-tests",
                                     current_build_num)
        self.wait_till_job_completes("zuul-demo-unit-tests",
                                     current_build_num)

        reviewers = gu.getReviewers(change_id)
        assert 'jenkins' in reviewers

        approvals = gu.getReviewerApprovals(change_id, 'jenkins')
        assert approvals['Verified'] == '+1'

        gu.delPubKey(k_index)
