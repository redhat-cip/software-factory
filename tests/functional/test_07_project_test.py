#!/bin/env python
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

from utils import Base
from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import JenkinsUtils
from utils import copytree

from pysflib.sfgerrit import GerritUtils


class TestProjectTestsWorkflow(Base):
    """ Functional tests to verify the configuration of a project test
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_URL)
        cls.sample_project_dir = \
            os.path.join(config.SF_TESTS_DIR, "sample_project/")

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []
        self.un = config.ADMIN_USER
        self.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[self.un]['auth_cookie'])
        self.gu2 = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.USER_2]['auth_cookie'])
        self.ju = JenkinsUtils()
        self.gu.add_pubkey(config.USERS[self.un]["pubkey"])
        priv_key_path = set_private_key(config.USERS[self.un]["privkey"])
        self.gitu_admin = GerritGitUtils(self.un,
                                         priv_key_path,
                                         config.USERS[self.un]['email'])
        # Clone the config repo and make change to it
        # in order to test the new sample_project
        self.config_clone_dir = self.clone_as_admin("config")
        self.original_layout = file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml")).read()
        self.original_zuul_projects = file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml")).read()
        self.original_project = file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml")).read()
        # Put USER_2 as core for config project
        self.gu.add_group_member(config.USER_2, "config-core")

    def tearDown(self):
        self.restore_config_repo(self.original_layout,
                                 self.original_project,
                                 self.original_zuul_projects)
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def clone_as_admin(self, pname):
        url = "ssh://%s@%s:29418/%s" % (self.un, config.GATEWAY_HOST,
                                        pname)
        clone_dir = self.gitu_admin.clone(url, pname)
        if os.path.dirname(clone_dir) not in self.dirs_to_delete:
            self.dirs_to_delete.append(os.path.dirname(clone_dir))
        return clone_dir

    def restore_config_repo(self, layout, project, zuul):
        file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml"), 'w').write(
            layout)
        file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml"), 'w').write(
            zuul)
        file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml"), 'w').write(
            project)
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

    def create_project(self, name, user,
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
        self.create_project(pname, config.ADMIN_USER)

        # Add the sample-project to the empty repository
        clone_dir = self.clone_as_admin("sample_project")
        copytree(self.sample_project_dir, clone_dir)
        self.commit_direct_push_as_admin(clone_dir, "Add the sample project")

        # Change to config/zuul/layout.yaml and jobs/projects.yaml
        # in order to test the new sample_project
        ycontent = file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml")).read()
        file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml"), 'w').write(
            ycontent.replace("zuul-demo", "sample_project")
        )
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
        last_success_build_num_ch = \
            self.ju.get_last_build_number("config-check",
                                          "lastSuccessfulBuild")
        # Retrieve the previous build number for config-update
        last_success_build_num_cu = \
            self.ju.get_last_build_number("config-update",
                                          "lastSuccessfulBuild")

        # Send review (config-check) will be triggered
        self.push_review_as_admin(
            self.config_clone_dir,
            "Add config definition in Zuul/JJB config for sample_project")

        # Wait for config-check to finish and verify the success
        self.ju.wait_till_job_completes("config-check",
                                        last_success_build_num_ch,
                                        "lastSuccessfulBuild")

        last_build_num_ch, last_success_build_num_ch = 0, 1
        attempt = 0
        while last_build_num_ch != last_success_build_num_ch:
            if attempt >= 90:
                break
            time.sleep(1)
            last_build_num_ch = \
                self.ju.get_last_build_number("config-check",
                                              "lastBuild")
            last_success_build_num_ch = \
                self.ju.get_last_build_number("config-check",
                                              "lastSuccessfulBuild")
            attempt += 1

        self.assertEqual(last_build_num_ch, last_success_build_num_ch)
        # let some time to Zuul to update the test result to Gerrit.
        time.sleep(2)

        # Get the change id
        change_ids = self.gu.get_my_changes_for_project("config")
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]

        # Check whether zuul sets verified to +1 after running the tests
        # let some time to Zuul to update the test result to Gerrit.
        attempt = 0
        while self.gu.get_reviewer_approvals(change_id, 'jenkins')['Verified'] \
                != '+1':
            if attempt >= 90:
                break
            time.sleep(1)
            attempt += 1

        self.assertEqual(
            self.gu.get_reviewer_approvals(change_id, 'jenkins')['Verified'],
            "+1")

        # review the change
        self.gu2.submit_change_note(change_id, "current", "Code-Review", "2")
        self.gu2.submit_change_note(change_id, "current", "Workflow", "1")

        # now zuul processes gate pipeline and runs config-check job
        # Wait for config-check to finish and verify the success
        self.ju.wait_till_job_completes("config-check",
                                        last_success_build_num_ch,
                                        "lastSuccessfulBuild")

        last_build_num_ch, last_success_build_num_ch = 0, 1
        attempt = 0
        while last_build_num_ch != last_success_build_num_ch:
            if attempt >= 90:
                break
            time.sleep(1)
            last_build_num_ch = \
                self.ju.get_last_build_number("config-check",
                                              "lastBuild")
            last_success_build_num_ch = \
                self.ju.get_last_build_number("config-check",
                                              "lastSuccessfulBuild")
            attempt += 1

        self.assertEqual(last_build_num_ch, last_success_build_num_ch)

        # Check whether zuul sets verified to +2 after running the tests
        # let some time to Zuul to update the test result to Gerrit.
        attempt = 0
        while self.gu.get_reviewer_approvals(change_id, 'jenkins')['Verified'] \
                != '+2':
            if attempt >= 90:
                break
            time.sleep(1)
            attempt += 1

        self.assertEqual(
            self.gu.get_reviewer_approvals(change_id, 'jenkins')['Verified'],
            "+2")

        # verify whether zuul merged the patch
        change = self.gu.get_change('config', 'master', change_id)
        change_status = change['status']
        attempt = 0
        while change_status != 'MERGED':
            if attempt >= 90:
                break
            time.sleep(1)
            change = self.gu.get_change('config', 'master', change_id)
            change_status = change['status']
            attempt += 1
        self.assertEqual(change_status, 'MERGED')

        # Test post pipe line
        # as the patch is merged, post pieline should run config-update job
        # Wait for config-update to finish and verify the success
        self.ju.wait_till_job_completes("config-update",
                                        last_success_build_num_cu,
                                        "lastSuccessfulBuild")
        last_build_num_cu = \
            self.ju.get_last_build_number("config-update",
                                          "lastBuild")
        last_success_build_num_cu = \
            self.ju.get_last_build_number("config-update",
                                          "lastSuccessfulBuild")
        self.assertEqual(last_build_num_cu, last_success_build_num_cu)

        # Retrieve the prev build number for sample_project-unit-tests
        # Retrieve the prev build number for sample_project-functional-tests
        last_success_build_num_sp_ut = \
            self.ju.get_last_build_number("sample_project-unit-tests",
                                          "lastSuccessfulBuild")
        last_success_build_num_sp_ft = \
            self.ju.get_last_build_number("sample_project-functional-tests",
                                          "lastSuccessfulBuild")
        # Test config-update
        # config-update should have created jobs for sample_project
        # Trigger tests on sample_project
        # Send a review and check tests has been run
        self.gitu_admin.add_commit_and_publish(
            clone_dir, 'master', "Add useless file",
            self.un)
        # Wait for sample_project-unit-tests to finish and verify the success
        self.ju.wait_till_job_completes("sample_project-unit-tests",
                                        last_success_build_num_sp_ut,
                                        "lastSuccessfulBuild")
        # Wait for sample_project-functional-tests to end and check the success
        self.ju.wait_till_job_completes("sample_project-functional-tests",
                                        last_success_build_num_sp_ft,
                                        "lastSuccessfulBuild")
        # Check the unit tests succeed
        last_build_num_sp_ut = \
            self.ju.get_last_build_number("sample_project-unit-tests",
                                          "lastBuild")
        last_success_build_num_sp_ut = \
            self.ju.get_last_build_number("sample_project-unit-tests",
                                          "lastSuccessfulBuild")
        self.assertEqual(last_build_num_sp_ut, last_success_build_num_sp_ut)
        # Check the functional tests succeed
        last_build_num_sp_ft = \
            self.ju.get_last_build_number("sample_project-functional-tests",
                                          "lastBuild")
        last_success_build_num_sp_ft = \
            self.ju.get_last_build_number("sample_project-functional-tests",
                                          "lastSuccessfulBuild")
        self.assertEqual(last_build_num_sp_ft, last_success_build_num_sp_ft)

        # Get the change id
        change_ids = self.gu.get_my_changes_for_project("sample_project")
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]

        # let some time to Zuul to update the test result to Gerrit.
        attempt = 0
        while "jenkins" not in self.gu.get_reviewers(change_id):
            if attempt >= 90:
                break
            time.sleep(1)
            attempt += 1

        attempt = 0
        while self.gu.get_reviewer_approvals(change_id, 'jenkins')['Verified'] \
                != '+1':
            if attempt >= 90:
                break
            time.sleep(1)
            attempt += 1

        self.assertEqual(
            self.gu.get_reviewer_approvals(change_id, 'jenkins')['Verified'],
            "+1")
