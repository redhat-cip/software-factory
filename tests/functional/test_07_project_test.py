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
import copy
import shutil
import time
from yaml import load, dump
import requests as http

from utils import Base
from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import GerritUtil
from utils import copytree


class TestProjectTestsWorkflow(Base):
    """ Functional tests to verify the configuration of a project test
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.MANAGESF_HOST, 80)
        cls.sample_project_dir = \
            os.path.join(os.environ["SF_ROOT"], "tests/sample_project/")

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []
        self.un = config.ADMIN_USER
        self.gu = GerritUtil(config.GERRIT_SERVER, username=self.un)
        self.gu2 = GerritUtil(config.GERRIT_SERVER, username=config.USER_2)
        self.gu.addPubKey(config.USERS[self.un]["pubkey"])
        priv_key_path = set_private_key(config.USERS[self.un]["privkey"])
        self.gitu_admin = GerritGitUtils(self.un,
                                         priv_key_path,
                                         config.USERS[self.un]['email'])
        # Clone the config repo and make change to it
        # in order to test the new sample_project
        self.config_clone_dir = self.clone_as_admin("config")
        self.original_layout = file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml")).read()
        self.original_project = file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml")).read()
        # Put USER_2 as core for config project
        self.gu.addGroupMember(config.USER_2, "config-core")

    def tearDown(self):
        self.restore_config_repo(self.original_layout,
                                 self.original_project)
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def clone_as_admin(self, pname):
        url = "ssh://%s@%s/%s" % (self.un, config.GERRIT_HOST,
                                  pname)
        clone_dir = self.gitu_admin.clone(url, pname)
        if os.path.dirname(clone_dir) not in self.dirs_to_delete:
            self.dirs_to_delete.append(os.path.dirname(clone_dir))
        return clone_dir

    def restore_config_repo(self, layout_content, project_content):
        file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml"), 'w').write(
            layout_content)
        file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml"), 'w').write(
            project_content)
        self.commit_direct_push_as_admin(
            self.config_clone_dir,
            "Restore layout.yaml and projects.yaml")

    def commit_direct_push_as_admin(self, clone_dir, msg):
        # Stage, commit and direct push the additions on master
        self.gitu_admin.add_commit_for_all_new_additions(clone_dir, msg)
        self.gitu_admin.direct_push_branch(clone_dir, 'master')

    def push_review_as_admin(self, clone_dir, msg):
        # Stage, commit and direct push the additions on master
        self.gitu_admin.add_commit_for_all_new_additions(clone_dir, msg)
        self.gitu_admin.review_push_branch(clone_dir, 'master')

    def get_last_build_number(self, job_name, type):
        url = config.JENKINS_SERVER
        url += "/job/%(job_name)s/%(type)s/buildNumber" \
               % {'job_name': job_name, 'type': type}
        try:
            resp = http.get(url)
            return int(resp.text)
        except:
            return 0

    def wait_till_job_completes(self, job_name, last, type):
        retries = 0
        while True:
            cur = self.get_last_build_number(job_name, type)
            if cur > last:
                # give some time to zuul to update score on gerrit
                time.sleep(2)
                break
            elif retries > 30:
                break
            else:
                time.sleep(1)
                retries += 1

    def createProject(self, name, user,
                      options=None):
        self.msu.createProject(name, user,
                               options)
        self.projects.append(name)

    def test_check_project_test_workflow(self):
        """ Validate new project to test via zuul layout.yaml
        """
        # We want to create a project, provide project source
        # code with tests. We then configure zuul/jjb to handle the
        # run of the test cases. We then validate Gerrit has been
        # updated about the test results
        # We use the sample-project (that already exists)

        pname = 'sample_project'
        # Be sure the project does not exist
        self.msu.deleteProject(pname,
                               config.ADMIN_USER)
        # Create it
        self.createProject(pname, config.ADMIN_USER)

        # Add the sample-project to the empty repository
        clone_dir = self.clone_as_admin("sample_project")
        copytree(self.sample_project_dir, clone_dir)
        self.commit_direct_push_as_admin(clone_dir, "Add the sample project")

        # Change to config/zuul/layout.yaml and jobs/projects.yaml
        # in order to test the new sample_project
        ycontent = load(file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml")).read())
        sp = copy.deepcopy(
            [p for p in ycontent['projects'] if p['name'] == 'zuul-demo'][0])
        sp['name'] = "sample_project"
        sp['check'][0] = sp['check'][0].replace('zuul-demo', 'sample_project')
        sp['check'][1] = sp['check'][1].replace('zuul-demo', 'sample_project')
        ycontent['projects'].append(sp)
        file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml"), 'w').write(
            dump(ycontent))
        ycontent2 = load(file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml")).read())
        sp2 = copy.deepcopy(
            [p for p in ycontent2 if p['project']['name'] == 'zuul-demo'][0])
        sp2['project']['name'] = "sample_project"
        ycontent2.append(sp2)
        file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml"), 'w').write(
            dump(ycontent2))

        # Retrieve the previous build number for config-check
        last_build_num_ch = \
            self.get_last_build_number("config-check",
                                       "lastBuild")
        # Retrieve the previous build number for config-update
        last_build_num_cu = \
            self.get_last_build_number("config-update",
                                       "lastBuild")

        # Send review (config-check) will be triggered
        self.push_review_as_admin(
            self.config_clone_dir,
            "Add config definition in Zuul/JJB config for sample_project")

        # Wait for config-check to finish and verify the success
        self.wait_till_job_completes("config-check",
                                     last_build_num_ch,
                                     "lastBuild")
        last_build_num_ch = \
            self.get_last_build_number("config-check",
                                       "lastBuild")
        last_success_build_num_ch = \
            self.get_last_build_number("config-check",
                                       "lastSuccessfulBuild")
        self.assertEqual(last_build_num_ch, last_success_build_num_ch)
        # let some time to Zuul to update the test result to Gerrit.
        time.sleep(2)

        # Get the change id
        change_ids = self.gu.getMyChangesForProject("config")
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]
        self.gu.setPlus2CodeReview(change_id, "current")
        self.gu.setPlus1Approved(change_id, "current")
        self.gu2.setPlus2CodeReview(change_id, "current")
        self.assertEqual(
            self.gu.submitPatch(change_id, "current")['status'], 'MERGED')

        # Wait for config-update to finish and verify the success
        self.wait_till_job_completes("config-update",
                                     last_build_num_cu,
                                     "lastBuild")
        last_build_num_cu = \
            self.get_last_build_number("config-update",
                                       "lastBuild")
        last_success_build_num_cu = \
            self.get_last_build_number("config-update",
                                       "lastSuccessfulBuild")
        self.assertEqual(last_build_num_cu, last_success_build_num_cu)

        # Retrieve the prev build number for sample_project-unit-tests
        # Retrieve the prev build number for sample_project-functional-tests
        last_build_num_sp_ut = \
            self.get_last_build_number("sample_project-unit-tests",
                                       "lastBuild")
        last_build_num_sp_ft = \
            self.get_last_build_number("sample_project-functional-tests",
                                       "lastBuild")
        # Trigger tests on sample_project
        # Send a review and check tests has been run
        self.gitu_admin.add_commit_and_publish(
            clone_dir, 'master', "Add useless file",
            self.un)
        # Wait for sample_project-unit-tests to finish and verify the success
        self.wait_till_job_completes("sample_project-unit-tests",
                                     last_build_num_sp_ut,
                                     "lastBuild")
        # Wait for sample_project-functional-tests to end and check the success
        self.wait_till_job_completes("sample_project-functional-tests",
                                     last_build_num_sp_ft,
                                     "lastBuild")
        # Check the unit tests succeed
        last_build_num_sp_ut = \
            self.get_last_build_number("sample_project-unit-tests",
                                       "lastBuild")
        last_success_build_num_sp_ut = \
            self.get_last_build_number("sample_project-unit-tests",
                                       "lastSuccessfulBuild")
        self.assertEqual(last_build_num_sp_ut, last_success_build_num_sp_ut)
        # Check the functional tests succeed
        last_build_num_sp_ft = \
            self.get_last_build_number("sample_project-functional-tests",
                                       "lastBuild")
        last_success_build_num_sp_ft = \
            self.get_last_build_number("sample_project-functional-tests",
                                       "lastSuccessfulBuild")
        self.assertEqual(last_build_num_sp_ft, last_success_build_num_sp_ft)

        # let some time to Zuul to update the test result to Gerrit.
        time.sleep(2)
        # Get the change id
        change_ids = self.gu.getMyChangesForProject("sample_project")
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]
        self.assertEqual(
            self.gu.getReviewerApprovals(change_id, 'jenkins')['Verified'],
            "+1")
