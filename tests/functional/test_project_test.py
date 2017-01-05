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
import re
import config
import copy
import shutil
import logging
import time
import requests
from yaml import load, dump

from utils import Base
from utils import set_private_key
from utils import ResourcesUtils
from utils import GerritGitUtils
from utils import JenkinsUtils
from utils import copytree
from utils import create_random_str
from utils import get_cookie

from pysflib.sfgerrit import GerritUtils


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestProjectTestsWorkflow(Base):
    """ Functional tests to verify the configuration of a project test
    """
    @classmethod
    def setUpClass(cls):
        cls.ru = ResourcesUtils()
        cls.sample_project_dir = \
            os.path.join(config.SF_TESTS_DIR, "sample_project/")

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        super(TestProjectTestsWorkflow, self).setUp()
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
        # Clone the config repo and keep job/zuul config content
        self.config_clone_dir = self.clone_as_admin("config")
        self.original_zuul_projects = file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml")).read()
        self.original_project = file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml")).read()
        self.need_restore_config_repo = False
        # Put USER_2 as core for config project
        self.gu.add_group_member(config.USER_2, "config-core")

    def tearDown(self):
        super(TestProjectTestsWorkflow, self).tearDown()
        if self.need_restore_config_repo:
            self.restore_config_repo(self.original_project,
                                     self.original_zuul_projects)
        for name in self.projects:
            self.ru.direct_delete_repo(name)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def assert_reviewer_approvals(self, change_id, value):
        approvals = {}
        for _ in range(300):
            approvals = self.gu.get_reviewer_approvals(change_id,
                                                       'jenkins')
            if approvals and approvals.get('Verified') == value:
                break
            time.sleep(1)
        self.assertEqual(value, approvals.get('Verified'))

    def clone_as_admin(self, pname):
        url = "ssh://%s@%s:29418/%s" % (self.un, config.GATEWAY_HOST,
                                        pname)
        clone_dir = self.gitu_admin.clone(url, pname)
        if os.path.dirname(clone_dir) not in self.dirs_to_delete:
            self.dirs_to_delete.append(os.path.dirname(clone_dir))
        return clone_dir

    def restore_config_repo(self, project, zuul):
        logger.info("Restore {zuul,jobs}/projects.yaml")
        file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml"), 'w').write(
            zuul)
        file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml"), 'w').write(
            project)
        change_sha = self.commit_direct_push_as_admin(
            self.config_clone_dir,
            "Restore {zuul,jobs}/projects.yaml")
        logger.info("Waiting for config-update on %s" % change_sha)
        self.ju.wait_for_config_update(change_sha)

    def commit_direct_push_as_admin(self, clone_dir, msg):
        # Stage, commit and direct push the additions on master
        self.gitu_admin.add_commit_for_all_new_additions(clone_dir, msg)
        return self.gitu_admin.direct_push_branch(clone_dir, 'master')

    def push_review_as_admin(self, clone_dir, msg):
        # Stage, commit and direct push the additions on master
        self.gitu_admin.add_commit_for_all_new_additions(clone_dir, msg)
        return self.gitu_admin.review_push_branch(clone_dir, 'master')

    def create_project(self, name):
        self.ru.direct_create_repo(name)
        self.projects.append(name)

    def test_timestamped_logs(self):
        """Test that jenkins timestamps logs"""
        # Done here to make sure a config-update job was run and to avoid
        # duplicating code
        timestamp_re = re.compile('\d{2}:\d{2}:\d{2}.\d{0,3}')
        n = self.ju.get_last_build_number("config-update",
                                          "lastBuild")
        cu_logs = self.ju.get_job_logs("config-update",
                                       n)
        self.assertTrue(cu_logs is not None)
        for l in cu_logs.split('\n'):
            if l:
                self.assertRegexpMatches(l, timestamp_re, msg=l)

    def test_check_project_test_workflow(self):
        """ Validate new project to test via zuul
        """
        # We want to create a project, provide project source
        # code with tests. We then configure zuul/jjb to handle the
        # run of the test cases. We then validate Gerrit has been
        # updated about the test results
        # We use the sample-project (that already exists)

        pname = 'test_workflow_%s' % create_random_str()
        logger.info("Creating project %s" % pname)

        # Create it
        self.create_project(pname)

        logger.info("Populating the project with %s" %
                    self.sample_project_dir)
        # Add the sample-project to the empty repository
        clone_dir = self.clone_as_admin(pname)
        copytree(self.sample_project_dir, clone_dir)
        self.commit_direct_push_as_admin(clone_dir, "Add the sample project")

        # Change to config/{zuul,jobs}/projects.yaml
        # in order to test the new project
        logger.info("Adding config-repo configuration")
        ycontent = file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml")).read()
        file(os.path.join(
            self.config_clone_dir, "zuul/projects.yaml"), 'w').write(
            ycontent.replace("zuul-demo", pname),
        )
        ycontent2 = load(file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml")).read())
        sp2 = copy.deepcopy(
            [p for p in ycontent2 if 'project' in p and
                p['project']['name'] == 'zuul-demo'][0])
        sp2['project']['name'] = pname
        ycontent2.append(sp2)
        file(os.path.join(
            self.config_clone_dir, "jobs/projects.yaml"), 'w').write(
            dump(ycontent2))

        # Send review (config-check) will be triggered
        logger.info("Submitting the config review")
        change_sha = self.push_review_as_admin(
            self.config_clone_dir,
            "Add config definition in Zuul/JJB config for %s" % pname)

        change_nr = self.gu.get_change_number(change_sha)

        logger.info("Waiting for verify +1 on change %d" % change_nr)
        self.assertEquals(self.gu.wait_for_verify(change_nr), 1)

        # review the config change as a member from the config-core group
        logger.info("Approving and waiting for verify +2")
        self.gu2.submit_change_note(change_nr, "current", "Code-Review", "2")
        self.gu2.submit_change_note(change_nr, "current", "Workflow", "1")

        for retry in xrange(60):
            jenkins_vote = self.gu.get_vote(change_nr, "Verified")
            if jenkins_vote == 2:
                break
            time.sleep(1)
        self.assertEquals(jenkins_vote, 2)

        # verify whether zuul merged the patch
        logger.info("Waiting for change to be merged")
        for retry in xrange(60):
            change_status = self.gu.get_info(change_nr)['status']
            if change_status == "MERGED":
                break
            time.sleep(1)
        self.assertEqual(change_status, 'MERGED')
        self.need_restore_config_repo = True

        logger.info("Waiting for config-update")
        config_update_log = self.ju.wait_for_config_update(change_sha)
        self.assertIn("Finished: SUCCESS", config_update_log)

        # Propose a change on a the repo and expect a Verified +1
        logger.info("Submiting a test change to %s" % pname)
        change_sha = self.gitu_admin.add_commit_and_publish(
            clone_dir, 'master', "Add useless file",
            self.un)

        change_nr = self.gu.get_change_number(change_sha)

        logger.info("Waiting for verify +1 on change %d" % change_nr)
        self.assertEquals(self.gu.wait_for_verify(change_nr), 1)

        # Update the change on a the repo and expect a Verified -1
        logger.info("Submiting a test change to %s suppose to fail" % pname)
        data = "#!/bin/bash\nexit 1\n"
        file(os.path.join(clone_dir, "run_tests.sh"), 'w').write(data)
        os.chmod(os.path.join(clone_dir, "run_tests.sh"), 0755)
        self.gitu_admin.add_commit_and_publish(
            clone_dir, "master", None, fnames=["run_tests.sh"])

        logger.info("Waiting for verify -1 on change %d" % change_nr)
        self.assertEquals(self.gu.wait_for_verify(change_nr), -1)

        logger.info("Validate jobs ran via the job api %s" % pname)
        # This piece of code is there by convenience ...
        # TODO: Should be moved in the job api tests file.
        # Test the manageSF jobs API: query per patch & revision
        change_ids = self.gu.get_my_changes_for_project(pname)
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]
        patch = self.gu.get_change_last_patchset(change_id)['_number']
        cookie = get_cookie(config.ADMIN_USER, config.ADMIN_PASSWORD)
        cookies = {"auth_pubtkt": cookie}
        base_url = config.GATEWAY_URL + "/manage/jobs/"
        for j in ["%s-functional-tests" % pname, "%s-unit-tests" % pname]:
            job = requests.get(base_url + '%s/?change=%s' % (j, patch),
                               cookies=cookies).json()
            self.assertTrue("jenkins" in job.keys(),
                            job)
            self.assertTrue(len(job["jenkins"]) > 1,
                            job)
