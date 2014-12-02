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

import config

from utils import Base
from utils import ManageSfUtils
from utils import create_random_str

from pysflib.sfredmine import RedmineUtils
from pysflib.sfgerrit import GerritUtils


class TestProjectMembership(Base):
    """ Functional tests that validate adding or deleting
    users to project groups using managesf.
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_HOST, 80)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.rm = RedmineUtils(
            config.REDMINE_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.gu = GerritUtils(
            'http://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)

    def create_project(self, name, user,
                       options=None):
        self.msu.createProject(name, user,
                               options)
        self.projects.append(name)

    def test_admin_manage_project_members(self):
        """ Test admin can add and delete users from all project groups
        """
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.ADMIN_USER)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))
        groups = 'ptl-group,core-group'
        # Add user2 to ptl and core groups
        self.msu.addUsertoProjectGroups(config.ADMIN_USER, pname,
                                        config.USER_2, groups)
        # Test if user2 exists in ptl and core groups
        self.assertTrue(self.gu.member_in_group(config.USER_2,
                                                '%s-ptl' % pname))
        self.assertTrue(self.gu.member_in_group(config.USER_2,
                                                '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_2, 'Manager'))
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_2, 'Developer'))

        # Delete user2 from project groups
        self.msu.deleteUserFromProjectGroups(config.ADMIN_USER, pname,
                                             config.USER_2)
        # Test if user exists in ptl and core groups
        self.assertFalse(self.gu.member_in_group(config.USER_2,
                                                 '%s-ptl' % pname))
        self.assertFalse(self.gu.member_in_group(config.USER_2,
                                                 '%s-core' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_2, 'Manager'))
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_2, 'Developer'))

    def test_ptl_manage_project_members(self):
        """ Test ptl can add and delete users from all project groups
        """
        # Let user2 create the project, so he will be ptl for this project
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.USER_2)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))
        groups = 'ptl-group,core-group'

        # ptl should be ale to add users to all groups
        # so user2 should be able to add user3 to ptl and core groups
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # Test if user3 exists in ptl and core groups
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-ptl' % pname))
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Manager'))
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Developer'))

        # ptl should be able to remove users from all groups
        self.msu.deleteUserFromProjectGroups(config.USER_2, pname,
                                             config.USER_3)
        # user3 shouldn't exist in any group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-ptl' % pname))
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-core' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Manager'))
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Developer'))

    def test_core_manage_project_members(self):
        """ Test core can add and delete users to core group
        """
        # let admin create the project
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.ADMIN_USER)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))
        groups = 'core-group'

        # Add user2 as core user
        self.msu.addUsertoProjectGroups(config.ADMIN_USER, pname,
                                        config.USER_2, groups)
        # Test if user2 exists in core group
        self.assertTrue(self.gu.member_in_group(config.USER_2,
                                                '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_2, 'Developer'))

        groups = 'core-group'
        # core should be ale to add users to only core group and not ptl group
        # so user2 should be able to add user3 to only core group and not
        # ptl group
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # user3 should exist in core group
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Developer'))

        groups = 'ptl-group'
        # core should not be allowed to add users to ptl group
        # so user2 should not be able to add user3 to ptl group
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # user3 shouldn't exist in ptl group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-ptl' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Manager'))

        # core should be able to remove users from core group
        group = 'core-group'
        self.msu.deleteUserFromProjectGroups(config.USER_2, pname,
                                             config.USER_3, group)
        # user3 shouldn't exist in core group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-core' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Developer'))

    def test_non_member_manage_project_members(self):
        """ Test non project members can add and delete users to core group
        """
        # Let admin create the project
        pname = 'p_%s' % create_random_str()
        self.create_project(pname, config.ADMIN_USER)
        # Gerrit part
        self.assertTrue(self.gu.project_exists(pname))
        self.assertTrue(self.gu.group_exists('%s-ptl' % pname))
        self.assertTrue(self.gu.group_exists('%s-core' % pname))

        # non project meber can't add user to core group
        # user2 can't add user3 to core group
        groups = 'core-group'
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # user3 shouldn't exist in core group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-core' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Developer'))

        groups = 'ptl-group'
        # non project meber can't add usr to ptl group
        # user2 can't add user3 to ptl group
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # user3 shouldn't exist in ptl group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-ptl' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Manager'))

        # non project meber can't delete usr from any group.
        # Let admin add user3 to ptl and core groups,
        # then try to remove user3 from ptl and core groups by
        # user2 (i.e non member user)
        groups = 'ptl-group,core-group'
        self.msu.addUsertoProjectGroups(config.ADMIN_USER, pname,
                                        config.USER_3, groups)
        # non-admin user(user2) can't remove users from project groups
        self.msu.deleteUserFromProjectGroups(config.USER_2, pname,
                                             config.USER_3)
        # user3 should exist in ptl and core group
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-ptl' % pname))
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-core' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Manager'))
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Developer'))

    def test_manage_project_members_for_dev_group(self):
        """ Add and Delete users from dev group by admin, ptl, core,
            dev and non members
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
        self.assertTrue(self.gu.member_in_group(config.ADMIN_USER,
                                                '%s-dev' % pname))
        # Redmine part
        self.assertTrue(self.rm.project_exists(pname))
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.ADMIN_USER,
                                                'Developer'))

        # Admin should add user to dev group
        groups = 'dev-group'
        self.msu.addUsertoProjectGroups(config.ADMIN_USER, pname,
                                        config.USER_3, groups)
        # Test if user3 exists in dev group
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-dev' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Developer'))

        # admin should be able to remove users from dev group
        self.msu.deleteUserFromProjectGroups(config.ADMIN_USER, pname,
                                             config.USER_3)
        # user3 shouldn't exist in dev group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-dev' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Developer'))

        # ptl should add user to dev group
        # let admin add user2 as ptl
        groups = 'ptl-group'
        self.msu.addUsertoProjectGroups(config.ADMIN_USER, pname,
                                        config.USER_2, groups)
        groups = 'dev-group'
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # Test if user3 exists in dev group
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-dev' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Developer'))

        # ptl should be able to remove users from dev group
        self.msu.deleteUserFromProjectGroups(config.USER_2, pname,
                                             config.USER_3)
        # user3 shouldn't exist in dev group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-dev' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Developer'))
        # Remove user2 as ptl
        self.msu.deleteUserFromProjectGroups(config.ADMIN_USER, pname,
                                             config.USER_2)

        # core should add user to dev group
        # let admin add user2 as core
        groups = 'core-group'
        self.msu.addUsertoProjectGroups(config.ADMIN_USER, pname,
                                        config.USER_2, groups)
        groups = 'dev-group'
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # Test if user3 exists in dev group
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-dev' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Developer'))

        # core should be able to remove users from dev group
        group = 'dev-group'
        self.msu.deleteUserFromProjectGroups(config.USER_2, pname,
                                             config.USER_3, group)
        # user3 shouldn't exist in dev group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-dev' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Developer'))
        # Remove user2 as core
        self.msu.deleteUserFromProjectGroups(config.ADMIN_USER, pname,
                                             config.USER_2)

        # let admin add user2 as developer
        groups = 'dev-group'
        self.msu.addUsertoProjectGroups(config.ADMIN_USER, pname,
                                        config.USER_2, groups)
        # dev user should be able to add a new user to dev group
        groups = 'dev-group'
        self.msu.addUsertoProjectGroups(config.USER_2, pname,
                                        config.USER_3, groups)
        # Test if user3 exists in dev group
        self.assertTrue(self.gu.member_in_group(config.USER_3,
                                                '%s-dev' % pname))
        # Redmine part
        self.assertTrue(self.rm.check_user_role(pname,
                                                config.USER_3, 'Developer'))

        # developer should be able to remove users from dev group
        group = 'dev-group'
        self.msu.deleteUserFromProjectGroups(config.USER_2, pname,
                                             config.USER_3, group)
        # user3 shouldn't exist in dev group
        self.assertFalse(self.gu.member_in_group(config.USER_3,
                                                 '%s-dev' % pname))
        # Redmine part
        self.assertFalse(self.rm.check_user_role(pname,
                                                 config.USER_3, 'Developer'))
        # Remove user2 ifrom dev group
        self.msu.deleteUserFromProjectGroups(config.ADMIN_USER, pname,
                                             config.USER_2)
