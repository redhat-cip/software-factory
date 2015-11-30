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
import shutil

import requests

from utils import Base
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import create_random_str
from utils import set_private_key

from pysflib.sfredmine import RedmineUtils
from pysflib.sfgerrit import GerritUtils


class TestManageSF(Base):
    """ Functional tests that validate managesf features.
    Here we do basic verifications about project creation
    with managesf.
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_URL)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []
        self.rm = RedmineUtils(
            config.GATEWAY_URL + "/redmine/",
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])

    def project_exists_ex(self, name, user):
        # Test here the project is "public"
        # ( Redmine API project detail does not return the private/public flag)
        rm = RedmineUtils(
            config.GATEWAY_URL + "/redmine/",
            auth_cookie=config.USERS[user]['auth_cookie'])
        try:
            return rm.project_exists(name)
        except Exception:
            return False

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def create_project(self, name, user, options=None):
        self.msu.createProject(name, user, options)
        self.projects.append(name)

    def test_create_public_project_as_admin(self):
        """ Create public project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.ADMIN_USER)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))
        # TODO(Project creator, as project owner, should only be in ptl group)
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-ptl' % pname))
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.project_exists(pname))
        self.assertTrue(
            self.rm.check_user_role(pname, config.ADMIN_USER, 'Manager'))
        self.assertTrue(
            self.rm.check_user_role(pname, config.ADMIN_USER, 'Developer'))
        self.assertTrue(self.project_exists_ex(pname, config.USER_2))

    def test_create_private_project_as_admin(self):
        """ Create private project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        options = {"private": ""}
        self.create_project(pname, config.ADMIN_USER,
                            options=options)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))
        self.assertTrue(self.gu.group_exists('%s-dev' % pname))
        # TODO(Project creator, as project owner, should only be in ptl group)
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-ptl' % pname))
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-core' % pname))
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-dev' % pname))
        # Redmine part
        self.assertTrue(self.rm.project_exists(pname))
        self.assertTrue(
            self.rm.check_user_role(pname, config.ADMIN_USER, 'Manager'))
        self.assertTrue(
            self.rm.check_user_role(pname, config.ADMIN_USER, 'Developer'))
        self.assertFalse(self.project_exists_ex(pname, config.USER_2))

    def test_delete_public_project_as_admin(self):
        """ Delete public project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.ADMIN_USER)
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.rm.project_exists(pname))
        self.msu.deleteProject(pname, config.ADMIN_USER)
        self.assertFalse(self.gu.project_exists(pname))
        self.assertFalse(self.gu.group_exists('%s-ptl' % pname))
        self.assertFalse(self.rm.project_exists(pname))
        self.assertFalse(self.gu.group_exists('%s-core' % pname))
        self.projects.remove(pname)

    def test_create_public_project_as_user(self):
        """ Create public project on redmine and gerrit as user
        """
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.USER_2)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))
        # TODO(Project creator, as project owner, should only be in ptl group)
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-ptl' % pname))
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.project_exists(pname))
        self.assertTrue(self.project_exists_ex(pname, config.USER_2))
        self.assertTrue(
            self.rm.check_user_role(pname, config.USER_2, 'Manager'))
        self.assertTrue(
            self.rm.check_user_role(pname, config.USER_2, 'Developer'))
        self.assertTrue(self.project_exists_ex(pname, config.USER_3))

    def test_create_private_project_as_user(self):
        """ Create private project on redmine and gerrit as user
        """
        pname = 'p_%s' % create_random_str()
        options = {"private": ""}
        self.create_project(pname, config.USER_2,
                            options=options)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))
        self.assertTrue(self.gu.group_exists('%s-dev' % pname))
        # TODO(Project creator, as project owner, should only be in ptl group)
        self.assertTrue(
            self.gu.member_in_group(config.USER_2, '%s-ptl' % pname))
        self.assertTrue(
            self.gu.member_in_group(config.USER_2, '%s-core' % pname))
        self.assertTrue(
            self.gu.member_in_group(config.USER_2, '%s-dev' % pname))
        # Redmine part
        self.assertTrue(self.rm.project_exists(pname))
        self.assertTrue(self.project_exists_ex(pname, config.USER_2))
        self.assertTrue(
            self.rm.check_user_role(pname, config.USER_2, 'Manager'))
        self.assertTrue(
            self.rm.check_user_role(pname, config.USER_2, 'Developer'))
        self.assertFalse(self.project_exists_ex(pname, config.USER_3))

    def test_create_public_project_with_users_in_group(self):
        """ Create public project on redmine and gerrit with users in groups
        """
        pname = 'p_%s' % create_random_str()
        u2mail = config.USERS[config.USER_2]['email']
        u3mail = config.USERS[config.USER_3]['email']
        options = {"ptl-group": "",
                   "core-group": "%s,%s" % (u2mail, u3mail),
                   }
        self.create_project(pname, config.ADMIN_USER,
                            options=options)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        # TODO(Project creator, as project owner, should only be in ptl group)
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-ptl' % pname))
        for user in (config.ADMIN_USER, config.USER_2, config.USER_3):
            self.assertTrue(self.gu.member_in_group(user, '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.project_exists(pname))
        self.assertTrue(
            self.rm.check_user_role(pname, config.ADMIN_USER, 'Manager'))
        for user in (config.ADMIN_USER, config.USER_2, config.USER_3):
            self.assertTrue(self.rm.check_user_role(pname, user, 'Developer'))

    def test_create_private_project_with_users_in_group(self):
        """ Create private project on redmine and gerrit with users in groups
        """
        pname = 'p_%s' % create_random_str()
        u2mail = config.USERS[config.USER_2]['email']
        u3mail = config.USERS[config.USER_3]['email']
        u4mail = config.USERS[config.USER_4]['email']
        options = {"private": "",
                   "ptl-group": "",
                   "core-group": "%s,%s" % (u2mail, u3mail),
                   "dev-group": "%s" % u4mail,
                   }
        self.create_project(pname, config.ADMIN_USER,
                            options=options)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        # TODO(Project creator, as project owner, should only be in ptl group)
        self.assertTrue(
            self.gu.member_in_group(config.ADMIN_USER, '%s-ptl' % pname))
        for user in (config.ADMIN_USER, config.USER_2, config.USER_3):
            self.assertTrue(self.gu.member_in_group(user, '%s-core' % pname))
        self.assertTrue(
            self.gu.member_in_group(config.USER_4, '%s-dev' % pname))
        # Redmine part
        # it should be visible to admin
        self.assertTrue(self.rm.project_exists(pname))
        self.assertTrue(
            self.rm.check_user_role(pname, config.ADMIN_USER, 'Manager'))
        for user in (config.ADMIN_USER, config.USER_2,
                     config.USER_3, config.USER_4):
            self.assertTrue(self.rm.check_user_role(pname, user, 'Developer'))

    def test_create_public_project_as_admin_clone_as_admin(self):
        """ Clone public project as admin and check content
        """
        pname = 'a_%s' % create_random_str()
        self.create_project(pname, config.ADMIN_USER)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, pname)
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))
        # Verify meta/config branch own both group and ACLs config file
        ggu.fetch_meta_config(clone_dir)
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'project.config')))
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'groups')))
        # There is no group dev for a public project
        content = file(os.path.join(clone_dir, 'project.config')).read()
        self.assertFalse('%s-dev' % pname in content)
        content = file(os.path.join(clone_dir, 'groups')).read()
        self.assertFalse('%s-dev' % pname in content)

    def test_create_private_project_as_admin_clone_as_admin(self):
        """ Clone private project as admin and check content
        """
        pname = 'p_%s' % create_random_str()
        options = {"private": ""}
        self.create_project(pname, config.ADMIN_USER, options=options)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, pname)
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))
        # Verify meta/config branch own both group and ACLs config file
        ggu.fetch_meta_config(clone_dir)
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'project.config')))
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'groups')))
        # There is a group dev for a private project
        content = file(os.path.join(clone_dir, 'project.config')).read()
        self.assertTrue('%s-dev' % pname in content)
        content = file(os.path.join(clone_dir, 'groups')).read()
        self.assertTrue('%s-dev' % pname in content)

    def test_create_public_project_as_admin_clone_as_user(self):
        """ Create public project as admin then clone as user
        """
        pname = 'p_%s' % create_random_str()
        # create the project as admin
        self.create_project(pname, config.ADMIN_USER)
        # add user2 ssh pubkey to user2
        gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.USER_2]['auth_cookie'])
        gu.add_pubkey(config.USER_2_PUB_KEY)
        # prepare to clone
        priv_key_path = set_private_key(config.USER_2_PRIV_KEY)
        self.dirs_to_delete.append(os.path.dirname(priv_key_path))
        ggu = GerritGitUtils(config.USER_2,
                             priv_key_path,
                             config.USERS[config.USER_2]['email'])
        url = "ssh://%s@%s:29418/%s" % (config.USER_2,
                                        config.GATEWAY_HOST, pname)
        # clone
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))

    def test_create_public_project_as_user_clone_as_user(self):
        """ Create public project as user then clone as user
        """
        pname = 'p_%s' % create_random_str()
        # create the project as admin
        self.create_project(pname, config.USER_2)
        # add user2 ssh pubkey to user2
        gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.USER_2]['auth_cookie'])
        gu.add_pubkey(config.USER_2_PUB_KEY)
        # prepare to clone
        priv_key_path = set_private_key(config.USER_2_PRIV_KEY)
        self.dirs_to_delete.append(os.path.dirname(priv_key_path))
        ggu = GerritGitUtils(config.USER_2,
                             priv_key_path,
                             config.USERS[config.USER_2]['email'])
        url = "ssh://%s@%s:29418/%s" % (config.USER_2,
                                        config.GATEWAY_HOST, pname)
        # clone
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))

    def test_upstream(self):
        """ Validate upstream feature of managesf
        """
        # Create a test upstream project
        pname_us = 'p_upstream'
        self.create_project(pname_us, config.ADMIN_USER)

        ggu_us = GerritGitUtils(config.ADMIN_USER,
                                config.ADMIN_PRIV_KEY_PATH,
                                config.USERS[config.ADMIN_USER]['email'])
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, pname_us)
        # clone
        us_clone_dir = ggu_us.clone(url, pname_us)
        self.dirs_to_delete.append(os.path.dirname(us_clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(us_clone_dir))
        # push some test files to the upstream project
        us_files = [str(x) for x in range(1, 10)]
        for f in us_files:
            file(os.path.join(us_clone_dir, f), 'w').write(f)
            os.chmod(os.path.join(us_clone_dir, f), 0755)

        ggu_us.add_commit_in_branch(us_clone_dir, "master",
                                    commit="Adding files 1-10",
                                    files=us_files)
        ggu_us.direct_push_branch(us_clone_dir, "master")
        ggu_us.add_commit_in_branch(us_clone_dir, "branch1")
        ggu_us.direct_push_branch(us_clone_dir, "branch1")

        # No create a test project with upstream pointing to the above
        upstream_url = "ssh://%s@%s:29418/%s" % (
            config.ADMIN_USER, config.GATEWAY_HOST, pname_us)
        pname = 'p_%s' % create_random_str()
        # create the project as admin
        options = {"upstream": upstream_url,
                   "upstream-ssh-key": config.ADMIN_PRIV_KEY_PATH}
        self.create_project(pname, config.ADMIN_USER, options=options)

        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, pname)
        # clone
        clone_dir = ggu.clone(url, pname)

        # Check if the files pushed in upstream project is present
        files = [f for f in os.listdir(clone_dir) if not f.startswith('.')]
        self.assertEqual(set(files), set(us_files))
        branches = ggu.get_branches(clone_dir, True)
        self.assertNotIn('gerrit/branch1', branches)

        # Test upstream with additional branches
        pname2 = 'p_%s' % create_random_str()
        options['add-branches'] = ''
        self.create_project(pname2, config.ADMIN_USER, options=options)
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, pname2)
        clone_dir = ggu.clone(url, pname2)
        branches = ggu.get_branches(clone_dir, True)
        self.assertIn('gerrit/branch1', branches)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

    def test_delete_project_as_admin(self):
        """ Check if admin can delete projects that are not owned by admin
        """
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.USER_2)
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.rm.project_exists(pname))
        self.msu.deleteProject(pname, config.ADMIN_USER)
        self.assertFalse(self.gu.project_exists(pname))
        self.assertFalse(self.gu.group_exists('%s-ptl' % pname))
        self.assertFalse(self.rm.project_exists(pname))
        self.assertFalse(self.gu.group_exists('%s-core' % pname))
        self.projects.remove(pname)

    def test_list_active_members(self):
        """ Check the list of members as a list of tuples of emails and names
        """
        self.assertTrue(self.msu.list_active_members(config.USER_2))

    def test_init_user_tests(self):
        """ Check if a test init feature behave as expected
        """
        project = 'p_%s' % create_random_str()
        self.create_project(project, config.USER_4)
        self.msu.create_init_tests(project, config.USER_4)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
        open_reviews = ggu.list_open_reviews('config', config.GATEWAY_HOST)
        match = [True for review in open_reviews if review['commitMessage'].
                 startswith("%s proposes initial test "
                            "definition for project %s" %
                            (config.USER_4, project))]
        self.assertEqual(len(match), 1)
        open_reviews = ggu.list_open_reviews(project, config.GATEWAY_HOST)
        match = [True for review in open_reviews if review['commitMessage'].
                 startswith("%s proposes initial test "
                            "scripts for project %s" %
                            (config.USER_4, project))]
        self.assertEqual(len(match), 1)

    def test_rest_urls_accessible(self):
        """ Check if managesf URLs are all working
        """
        project = 'p_%s' % create_random_str()
        self.create_project(project, config.ADMIN_USER)
        cookies = dict(
            auth_pubtkt=config.USERS[config.ADMIN_USER]['auth_cookie'])
        paths = [
            "/manage/project/",
            "/manage/project/%s" % project,
            "/manage/project/membership/"]
        for path in paths:
            url = "http://%s%s" % (config.GATEWAY_HOST, path)
            resp = requests.get(url, cookies=cookies)
            self.assertEqual(200, resp.status_code)

    def test_validate_get_all_project_details(self):
        """ Check if managesf allow us to fetch projects details
        """
        project = 'p_%s' % create_random_str()
        self.create_project(project, config.USER_2)
        admin_cookies = dict(
            auth_pubtkt=config.USERS[config.ADMIN_USER]['auth_cookie'])
        user2_cookies = dict(
            auth_pubtkt=config.USERS[config.USER_2]['auth_cookie'])
        url = "http://%s%s" % (config.GATEWAY_HOST, "/manage/project/")
        resp = requests.get(url, cookies=admin_cookies)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(project in resp.json())
        self.assertTrue('config' in resp.json())
        resp = requests.get(url, cookies=user2_cookies)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(project in resp.json())
        self.assertTrue('config' in resp.json())
        resp = requests.get(url, cookies=user2_cookies)
