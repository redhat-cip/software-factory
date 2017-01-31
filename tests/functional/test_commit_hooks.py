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

import config
import shutil
import time

from utils import Base
from utils import ResourcesUtils
from utils import GerritGitUtils
from utils import create_random_str
from utils import set_private_key
from utils import skipIfServiceMissing

from pysflib.sfgerrit import GerritUtils
from pysflib.sfstoryboard import SFStoryboard


TEST_MSGS = [
    ('Task: %(tid)s', 'merged'),
    ('Related-Task: %(tid)s', 'inprogress'),
]


class TestGerritHooks(Base):
    """ Functional tests that validate Gerrit hooks.
    """
    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []
        self.issues = []
        self.ru = ResourcesUtils()
        self.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.gu.add_pubkey(config.USERS[config.ADMIN_USER]["pubkey"])
        priv_key_path = set_private_key(
            config.USERS[config.ADMIN_USER]["privkey"])
        self.gitu = GerritGitUtils(config.ADMIN_USER,
                                   priv_key_path,
                                   config.USERS[config.ADMIN_USER]['email'])
        self.client_stb = SFStoryboard(
            config.GATEWAY_URL + "/storyboard_api",
            config.USERS[config.ADMIN_USER]['auth_cookie'])

    def tearDown(self):
        for issue in self.issues:
            self.client_stb.stories.get(id=issue[1]).tasks.delete(id=issue[0])
            self.client_stb.stories.delete(id=issue[1])
        for name in self.projects:
            self.ru.delete_repo(name)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def create_project(self, name):
        self.ru.create_repo(name)
        self.projects.append(name)

    def create_story(self, project, title):
        project = self.client_stb.projects.get(project)
        story = self.client_stb.stories.create(title=title)
        task = self.client_stb.tasks.create(
            story_id=story.id, project_id=project.id,
            title="%s - task 1" % title)
        return story.id, task.id

    def _test_update_issue_hooks(self, comment_template, status,
                                 pname):
        """ A referenced issue in commit msg triggers the hook
        """
        # Create the project
        self.create_project(pname)

        # Create an issue on the project
        sid, tid = self.create_story(pname, "There is a problem")
        self.issues.append((sid, tid))

        # Clone and commit something
        url = "ssh://%s@%s:29418/%s" % (
            config.ADMIN_USER, config.GATEWAY_HOST, pname)
        clone_dir = self.gitu.clone(url, pname)
        cmt_msg = comment_template % {'tid': tid, 'sid': sid}
        self.gitu.add_commit_and_publish(clone_dir, 'master', cmt_msg)

        # Check issue status (Gerrit hook updates the issue to in progress)
        for retry in xrange(10):
            task = self.client_stb.tasks.get(tid)
            if task.status == "inprogress":
                break
            time.sleep(1)
        self.assertEquals(task.status, "inprogress")
        self._test_merging(pname, tid, status)

    def _test_merging(self, pname, tid, status):
        # Get the change id and merge the patch
        change_ids = self.gu.get_my_changes_for_project(pname)
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]
        self.gu.submit_change_note(change_id, "current", "Code-Review", "2")
        self.gu.submit_change_note(change_id, "current", "Workflow", "1")
        self.gu.submit_change_note(change_id, "current", "Verified", "2")
        self.assertTrue(self.gu.submit_patch(change_id, "current"))

        # Check issue status (Gerrit hook updates the issue to in progress)
        for retry in xrange(10):
            task = self.client_stb.tasks.get(tid)
            if task.status == status:
                break
            time.sleep(1)
        self.assertEquals(task.status, status)

    @skipIfServiceMissing('storyboard')
    def test_gerrit_hook(self):
        """test various commit messages triggering a hook"""
        for template, final_status in TEST_MSGS:
            pname = create_random_str()
            self._test_update_issue_hooks(template, final_status, pname)

    @skipIfServiceMissing('storyboard')
    def test_gerrit_hook_double_quotes(self):
        """test commit messages with double quotes"""
        template, final_status = TEST_MSGS[0]
        verbose_template = """Super fix

This fix solves the Universe. Not just the "Universe", the Universe.
"""
        verbose_template += template
        pname = create_random_str()
        self._test_update_issue_hooks(verbose_template, final_status,
                                      pname)
