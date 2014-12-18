#!/usr/bin/env python
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

from unittest import TestCase
from mock import patch
from pecan.core import exc
from managesf.controllers import redminec
from managesf.tests import dummy_conf


class TestRedmine(TestCase):
    @classmethod
    def setupClass(cls):
        cls.conf = dummy_conf()
        redminec.conf = cls.conf

    @classmethod
    def tearDownClass(cls):
        pass

    def get_role_id_side_effect(*args, **kwargs):
        if args[0] is 'Manager':
            return 4
        elif args[0] is 'Developer':
            return 5
        else:
            return None

    @patch('managesf.controllers.redminec.add_user_to_projectgroups')
    @patch('managesf.controllers.redminec.RedmineUtils.create_project')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.get_user_id_by_username')
    @patch('managesf.controllers.redminec.request')
    @patch('redmine.managers.ResourceManager.get')
    def test_redmine_init_project(self, rget, request_mock,
                                  get_user_id_by_username_mock,
                                  create_project_mock, autg_mock):
        inp = {'description': 'demo project',
               'ptl-group-members': ['john@tests.dom'],
               'core-group-members': ['john@tests.dom']}
        request_mock.remote_user = 'user1'
        redminec.init_project('sf-demo', inp)
        create_project_mock.assert_called_once_with('sf-demo', 'demo project',
                                                    False)
        self.assertEqual(get_user_id_by_username_mock.call_count, 1)
        self.assertEqual(autg_mock.call_count, 4)

    @patch(
        'managesf.controllers.redminec.RedmineUtils.'
        'get_project_membership_for_user')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.'
        'get_project_roles_for_user')
    @patch('managesf.controllers.redminec.RedmineUtils.update_membership')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.update_project_membership')
    @patch('managesf.controllers.redminec.user_is_administrator')
    @patch('managesf.controllers.redminec.RedmineUtils.get_role_id')
    @patch('managesf.controllers.redminec.RedmineUtils.get_user_id')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.get_user_id_by_username')
    @patch('managesf.controllers.redminec.request')
    def test_redmine_add_user_to_projectgroups(
            self, request_mock, get_user_id_by_username_mock,
            get_user_id_mock, get_role_id_mock,
            user_is_administrator_mock, update_project_membership_mock,
            update_membership_mock, get_project_roles_for_user_mock,
            get_project_membership_for_user_mock):
        user2 = 'davis'
        user2_id = 102
        user2_mem_id = 2
        dev_role_id = 2
        get_user_id_mock.return_value = user2_id
        user_is_administrator_mock.return_value = False
        get_role_id_mock.return_value = dev_role_id

        # 401 error, when Develper try to add user to ptl group
        get_project_roles_for_user_mock.return_value = ['Developer']
        groups = ['ptl-group']
        self.assertRaises(exc.HTTPUnauthorized,
                          redminec.add_user_to_projectgroups,
                          'sf-demo', user2, groups)

        # 401 error, when non-member try to add user to any group
        get_project_roles_for_user_mock.return_value = []
        groups = ['core-group']
        self.assertRaises(exc.HTTPUnauthorized,
                          redminec.add_user_to_projectgroups,
                          'sf-demo', user2, groups)
        groups = ['ptl-group']
        self.assertRaises(exc.HTTPUnauthorized,
                          redminec.add_user_to_projectgroups,
                          'sf-demo', user2, groups)

        get_project_roles_for_user_mock.return_value = ['Manager']
        groups = ['core-group']
        # update_project_membership should be called when manager adds a user
        # who is not a member(i.e Mock returns None below),
        # manager adds developer/core to project
        get_project_membership_for_user_mock.return_value = None
        redminec.add_user_to_projectgroups('sf-demo', user2, groups)
        update_project_membership_mock.assert_called_once_with(
            'sf-demo', [{'user_id': user2_id, 'role_ids': [dev_role_id]}])

        # update_membership should be called when manager adds a user who is
        # already a project member(i.e
        # Mock returns his existing membership below),
        # manager adds developer/core to project
        get_project_membership_for_user_mock.return_value = user2_mem_id
        redminec.add_user_to_projectgroups('sf-demo', 'david', groups)
        update_membership_mock.assert_called_once_with(
            user2_mem_id,  [dev_role_id, dev_role_id])

    @patch('managesf.controllers.redminec.RedmineUtils.delete_membership')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.'
        'get_project_membership_for_user')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.'
        'get_project_roles_for_user')
    @patch('managesf.controllers.redminec.RedmineUtils.update_membership')
    @patch('managesf.controllers.redminec.user_is_administrator')
    @patch('managesf.controllers.redminec.RedmineUtils.get_role_id')
    @patch('managesf.controllers.redminec.RedmineUtils.get_user_id')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.get_user_id_by_username')
    @patch('managesf.controllers.redminec.request')
    def test_redmine_delete_user_from_projectgroups(
            self, request_mock, get_user_id_by_username,
            get_user_id_mock, get_role_id_mock,
            user_is_administrator_mock, update_membership_mock,
            get_project_roles_for_user_mock,
            get_project_membership_for_user_mock, delete_membership_mock):
        user2 = 'davis'
        user2_id = 102
        user2_mem_id = 2
        mgr_role_id = 1
        dev_role_id = 2
        get_user_id_mock.return_value = user2_id
        user_is_administrator_mock.return_value = False
        get_role_id_mock.return_value = dev_role_id

        # If no membership for the user, then it should return None
        get_project_membership_for_user_mock.return_value = None
        self.assertEqual(
            None, redminec.delete_user_from_projectgroups('sf-demo', user2,
                                                          'dev-group'))
        get_project_membership_for_user_mock.return_value = user2_mem_id
        # 401 error, when Developer try to delete user from ptl group
        get_project_roles_for_user_mock.return_value = ['Developer']
        self.assertRaises(exc.HTTPUnauthorized,
                          redminec.delete_user_from_projectgroups,
                          'sf-demo', user2, 'ptl-group')

        # 401 error, when non-member try to delete user from any group
        get_project_roles_for_user_mock.return_value = []
        self.assertRaises(exc.HTTPUnauthorized,
                          redminec.delete_user_from_projectgroups,
                          'sf-demo', user2, 'core-group')
        self.assertRaises(exc.HTTPUnauthorized,
                          redminec.delete_user_from_projectgroups,
                          'sf-demo', user2, 'ptl-group')

        # Delete from all groups
        get_project_roles_for_user_mock.return_value = ['Manager']
        redminec.delete_user_from_projectgroups('sf-demo', user2, None)
        delete_membership_mock.assert_called_once_with(user2_mem_id)

        returns = [['Manager'], ['Developer', 'Manager']]

        def side_effect(*args):
            result = returns.pop(0)
            return result

        returns2 = [dev_role_id, dev_role_id, mgr_role_id]

        def side_effect2(*args):
            result = returns2.pop(0)
            return result

        get_project_roles_for_user_mock.side_effect = side_effect
        get_role_id_mock.side_effect = side_effect2
        get_project_membership_for_user_mock.return_value = user2_mem_id
        redminec.delete_user_from_projectgroups('sf-demo', user2, 'core-group')
        update_membership_mock.assert_called_once_with(user2_mem_id,
                                                       [mgr_role_id])
        update_membership_mock.reset_mock()

        returns = [['Manager'], ['Developer', 'Manager']]
        returns2 = [mgr_role_id, dev_role_id, mgr_role_id]
        get_role_id_mock.return_value = mgr_role_id
        redminec.delete_user_from_projectgroups('sf-demo', user2, 'ptl-group')
        update_membership_mock.assert_called_once_with(user2_mem_id,
                                                       [dev_role_id])

    @patch(
        'managesf.controllers.redminec.RedmineUtils.'
        'get_project_roles_for_user')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.'
        'get_user_id')
    @patch('managesf.controllers.redminec.request')
    @patch(
        'managesf.controllers.redminec.RedmineUtils.get_user_id_by_username')
    def test_redmine_user_manages_project(
            self, get_user_id_by_username_mock,
            request_mock, get_user_id_mock,
            get_project_roles_for_user_mock):
        get_project_roles_for_user_mock.return_value = []
        # This call should return False
        self.assertEqual(False, redminec.user_manages_project('sf-demo'))
        get_project_roles_for_user_mock.return_value = ['Manager']
        # This call should return True
        self.assertEqual(True, redminec.user_manages_project('sf-demo'))

    @patch('managesf.controllers.redminec.request')
    def test_redmine_user_is_administrator(self, request_mock):
        request_mock.remote_user = 'user2'
        # This call should return False
        self.assertEqual(False, redminec.user_is_administrator())

        request_mock.remote_user = 'user1'
        # This call should return True
        self.assertEqual(True, redminec.user_is_administrator())

    @patch('managesf.controllers.redminec.RedmineUtils.delete_project')
    @patch('managesf.controllers.redminec.user_is_administrator')
    @patch('managesf.controllers.redminec.user_manages_project')
    def test_redmine_delete_project(self, user_manages_project_mock,
                                    user_is_administrator_mock,
                                    delete_project_mock):
        user_is_administrator_mock.return_value = False
        user_manages_project_mock.return_value = False
        self.assertRaises(exc.HTTPForbidden,
                          redminec.delete_project, 'sf-demo')
        user_manages_project_mock.return_value = True
        redminec.delete_project('sf-demo')
        self.assertTrue(delete_project_mock.called)
