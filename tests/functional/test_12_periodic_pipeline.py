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
from yaml import load, dump

from utils import Base
from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import JenkinsUtils

from pysflib.sfgerrit import GerritUtils


class TestZuulPeriodicPipeline(Base):
    """ Functional tests to verify the zuul periodic pipeline
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_HOST, 80)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []
        self.un = config.ADMIN_USER
        self.gu = GerritUtils(
            'http://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[self.un]['auth_cookie'])
        self.gu2 = GerritUtils(
            'http://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[config.USER_2]['auth_cookie'])
        self.ju = JenkinsUtils()
        self.gu.add_pubkey(config.USERS[self.un]["pubkey"])
        priv_key_path = set_private_key(config.USERS[self.un]["privkey"])
        self.gitu_admin = GerritGitUtils(self.un,
                                         priv_key_path,
                                         config.USERS[self.un]['email'])
        # Clone the config repo and change timer for periodic pipeline
        self.config_clone_dir = self.clone_as_admin("config")
        self.original_layout = file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml")).read()
        self.original_projects = file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml")).read()
        # Put USER_2 as core for config project
        self.gu.add_group_member(config.USER_2, "config-core")

    def tearDown(self):
        self.restore_config_repo(self.original_layout, self.original_projects)
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

    def restore_config_repo(self, layout_content, projects_content):
        file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml"), 'w').write(
            layout_content)
        file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml"), 'w').write(
            projects_content)
        self.commit_direct_push_as_admin(
            self.config_clone_dir,
            "Restore layout.yaml")

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

    def test_zuul_periodic_pipeline(self):
        """ Test zuul periodic pipeline
        """
        # We want to create a project with valid test files,
        # Then configure the periodic job for this project.
        # This periodic job is configured to run for each minute.
        # We check wether the job is ran for each minute
        # at the end of the test.

        pname = 'zuul-demo'
        # Create it
        self.create_project(pname, config.ADMIN_USER)

        # Create the zuul-demo project with test files
        # Later we wont submit files for review to trigger jenkins jobs.
        # Jenkins Jobs on this project will be triggered by zuul timer.
        clone_dir = self.clone_as_admin(pname)
        data = "echo Working"
        files = ["run_functional-tests.sh"]

        for f in files:
            file(os.path.join(clone_dir, f), 'w').write(data)
            os.chmod(os.path.join(clone_dir, f), 0755)

        self.commit_direct_push_as_admin(clone_dir,
                                         "Add files to zuul-demo project")

        # Change ther timer in config/zuul/layout.yaml
        # so that periodic jobs will be trigger for each minute
        ycontent = load(file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml")).read())
        for p in ycontent['pipelines']:
            if p['name'] == 'periodic':
                (p['trigger']['timer'][0])['time'] = '*/1 * * * *'
        file(os.path.join(
            self.config_clone_dir, "zuul/layout.yaml"), 'w').write(
            dump(ycontent))

        # Rewrite zuul/projects.yaml as well to keep the same indent
        ycontent2 = load(file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml")).read())
        file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml"), 'w').write(
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
            "Change timer in Zuul to trigger periodic jobs every minute")

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

        # review the change
        self.gu2.submit_change_note(change_id, "current", "Code-Review", "2")
        self.gu.submit_change_note(change_id, "current", "Code-Review", "2")
        self.gu2.submit_change_note(change_id, "current", "Workflow", "1")

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

        # As the patch is merged, post pieline should run config-update job
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

        # Now zuul periodic job will be run for every minute
        # Retrieve the prev build number for periodic-zuul-demo job
        last_success_build_num = \
            self.ju.get_last_build_number(
                "periodic-zuul-demo", "lastSuccessfulBuild")
        # periodic job runs for every 1 minute, so wait for 1 minute
        time.sleep(60)
        # Wait for periodic-zuul-demo to end and check the success
        self.ju.wait_till_job_completes("periodic-zuul-demo",
                                        last_success_build_num,
                                        "lastSuccessfulBuild")
        # Check the periodic functional tests succeed
        latest_success_build_num = \
            self.ju.get_last_build_number(
                "periodic-zuul-demo", "lastSuccessfulBuild")
        self.assertGreater(latest_success_build_num, last_success_build_num)
        last_success_build_num = latest_success_build_num
        last_build_num = \
            self.ju.get_last_build_number(
                "periodic-zuul-demo", "lastBuild")
        self.assertEqual(last_build_num, last_success_build_num)

        # wait for 1 more minute and check periodic job ran another time
        time.sleep(60)
        # Wait for periodic-zuul-demo to end and check the success
        self.ju.wait_till_job_completes("periodic-zuul-demo",
                                        last_success_build_num,
                                        "lastSuccessfulBuild")
        # Check the periodic functional tests succeed
        latest_success_build_num = \
            self.ju.get_last_build_number(
                "periodic-zuul-demo", "lastSuccessfulBuild")
        self.assertGreater(latest_success_build_num, last_success_build_num)
        last_success_build_num = latest_success_build_num
        last_build_num = \
            self.ju.get_last_build_number(
                "periodic-zuul-demo", "lastBuild")
        self.assertEqual(last_build_num, last_success_build_num)
