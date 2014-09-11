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
from mock import call
from pecan.core import exc
from managesf.controllers import redmine
import json


class dummy_conf():
    def __init__(self):
        self.redmine = {'api_key': 'XXX',
                        'host': 'redmine.tests.dom',
                        }
        self.admin = {'name': 'user1',
                      'email': 'user1@example.com',
                      'http_password': 'userpass',
                      'cookiejar': None}
        self.auth = {'host': 'auth.tests.dom'}


class FakeResponse():
    def __init__(self, code, content=None, text=None):
        self.status_code = code
        self.content = content
        self.text = text

    def json(self):
        return json.loads(self.content)


class TestRedmine(TestCase):
    @classmethod
    def setupClass(cls):
        cls.conf = dummy_conf()
        redmine.conf = cls.conf

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

    def test_redmine_create_project(self):
        def fake_send_request(url, ret, method, **kwargs):
            self.assertEqual(url,
                             'http://redmine.tests.dom/redmine/projects.json')
            self.assertEqual(method, 'POST')
            self.assertEqual(ret, [201])
            self.assertEqual(kwargs['headers']['Content-type'],
                             'application/xml')
            self.assertIn('data', kwargs)
            return FakeResponse(201)
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                redmine.create_project('sf-demo', 'demo project', False)

    def test_redmine_get_current_user_id(self):
        def fake_send_request(url, ret, method, **kwargs):
            url_match = 'http://redmine.tests.dom/redmine/users/current.json'
            self.assertEqual(url, url_match)
            self.assertEqual(method, 'GET')
            self.assertEqual(ret, [200])
            data = json.dumps({'user': {'id': 101}})
            return FakeResponse(200, data)
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                self.assertEqual(101, redmine.get_current_user_id())

    def test_redmine_get_user_id(self):
        def fake_send_request(url, ret, method, **kwargs):
            self.assertIn('davis', url)
            self.assertEqual(method, 'GET')
            self.assertEqual(ret, [200])
            data = {'total_count': 1,
                    'users': [{'id': 102}]}
            data = json.dumps(data)
            return FakeResponse(200, data)
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                self.assertEqual(102, redmine.get_user_id('davis'))

    def test_redmine_get_role_id(self):
        def fake_send_request(url, ret, method, **kwargs):
            url_match = 'http://redmine.tests.dom/redmine/roles.json'
            self.assertEqual(url, url_match)
            self.assertEqual(method, 'GET')
            self.assertEqual(ret, [200])
            data = json.dumps({'roles': [{'name': 'Manager', 'id': 4}]})
            return FakeResponse(200, data)
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                self.assertEqual(4, redmine.get_role_id('Manager'))
                self.assertEqual(None, redmine.get_role_id('Programmer'))

    def test_redmine_update_membership(self):
        def fake_send_request(url, ret, method, **kwargs):
            self.assertIn('1', url)
            self.assertEqual(method, 'PUT')
            self.assertEqual(ret, [200])
            data = {"membership": {"role_ids": [4]}}
            self.assertEqual(data, json.loads(kwargs['data']))
            return FakeResponse(200)
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                redmine.update_membership(1, [4])

    def test_redmine_edit_membership(self):
        def fake_send_request(url, ret, method, **kwargs):
            self.assertIn('sf-demo', url)
            self.assertEqual(method, 'POST')
            self.assertEqual(ret, [201])
            data = {"membership": {'user_id': 101, 'role_ids': [4, 5]}}
            self.assertEqual(data, json.loads(kwargs['data']))
            return FakeResponse(200)
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                memberships = [{'user_id': 101, 'role_ids': [4, 5]}]
                redmine.edit_membership('sf-demo', memberships)

    @patch('managesf.controllers.redmine.request')
    @patch('managesf.controllers.redmine.edit_membership')
    @patch('managesf.controllers.redmine.get_role_id')
    @patch('managesf.controllers.redmine.get_user_id')
    def test_redmine_update_project_roles(self, get_user_id_mock,
                                          get_role_id_mock,
                                          edit_membership_mock, request_mock):
        request_mock.remote_user = 'john'
        get_user_id_mock.return_value = 101
        # to return different id based on role name
        get_role_id_mock.side_effect = self.get_role_id_side_effect
        ptl = ['john']
        core = ['john']
        redmine.update_project_roles('sf-demo', ptl, core, [])
        # check redmine.get_user_id called
        self.assertEqual(True, get_user_id_mock.called)
        get_user_id_mock.called_with('john')
        # check get_role_id with Manager and Developer as arguments in sequence
        calls = [call('Manager'), call('Developer')]
        get_role_id_mock.assert_has_calls(calls, any_order=True)
        memberships = [{'user_id': 101, 'role_ids': [4, 5]}]
        edit_membership_mock.called_once_with('sf-demo', memberships)

    @patch('managesf.controllers.redmine.update_project_roles')
    @patch('managesf.controllers.redmine.create_project')
    def test_redmine_init_project(self, create_project_mock,
                                  update_project_roles_mock):
        inp = {'description': 'demo project',
               'ptl-group-members': ['john'],
               'core-group-members': ['john']}
        redmine.init_project('sf-demo', inp)
        create_project_mock.assert_called_once_with('sf-demo', 'demo project',
                                                    False)
        update_project_roles_mock.assert_called_once_with('sf-demo', ['john'],
                                                          ['john'], [])

    @patch('managesf.controllers.redmine.get_project_membership_for_user')
    @patch('managesf.controllers.redmine.get_project_roles_for_current_user')
    @patch('managesf.controllers.redmine.update_membership')
    @patch('managesf.controllers.redmine.edit_membership')
    @patch('managesf.controllers.redmine.user_is_administrator')
    @patch('managesf.controllers.redmine.get_role_id')
    @patch('managesf.controllers.redmine.get_user_id')
    def test_redmine_add_user_to_projectgroups(
            self, get_user_id_mock, get_role_id_mock,
            user_is_administrator_mock, edit_membership_mock,
            update_membership_mock, get_project_roles_for_current_user_mock,
            get_project_membership_for_user_mock):
        user2 = 'davis'
        user2_id = 102
        user2_mem_id = 2
        proj_id = 1
        mgr_role_id = 1
        dev_role_id = 2
        get_user_id_mock.return_value = user2_id
        user_is_administrator_mock.return_value = False
        get_role_id_mock.return_value = dev_role_id

        # 401 error, when Develper try to add user to ptl group
        get_project_roles_for_current_user_mock.return_value = ['Developer']
        groups = ['ptl-group']
        self.assertRaises(exc.HTTPUnauthorized,
                          redmine.add_user_to_projectgroups,
                          'sf-demo', user2, groups)

        # 401 error, when non-member try to add user to any group
        get_project_roles_for_current_user_mock.return_value = []
        groups = ['core-group']
        self.assertRaises(exc.HTTPUnauthorized,
                          redmine.add_user_to_projectgroups,
                          'sf-demo', user2, groups)
        groups = ['ptl-group']
        self.assertRaises(exc.HTTPUnauthorized,
                          redmine.add_user_to_projectgroups,
                          'sf-demo', user2, groups)

        get_project_roles_for_current_user_mock.return_value = ['Manager']
        groups = ['core-group']
        # edit_membership should be called when manager adds a user
        # who is not a member(i.e Mock returns None below),
        # manager adds developer/core to project
        get_project_membership_for_user_mock.return_value = None
        redmine.add_user_to_projectgroups('sf-demo', user2, groups)
        edit_membership_mock.assert_called_once_with(
            'sf-demo', [{'user_id': user2_id, 'role_ids': [dev_role_id]}])

        # update_membership should be called when manager adds a user who is
        # already a project member(i.e
        # Mock returns his existing membership below),
        # manager adds developer/core to project
        role = {'role': {'name': 'Manager', 'id': mgr_role_id}}
        membership = {'id': user2_mem_id,
                      'project': {'name': 'sf-demo', 'id': proj_id},
                      'user': {'name': 'david', 'id': user2_id},
                      'roles': [role]}
        get_project_membership_for_user_mock.return_value = membership
        redmine.add_user_to_projectgroups('sf-demo', 'david', groups)
        update_membership_mock.assert_called_once_with(
            user2_mem_id,  [dev_role_id])

    @patch('managesf.controllers.redmine.delete_membership')
    @patch('managesf.controllers.redmine.get_project_membership_for_user')
    @patch('managesf.controllers.redmine.get_project_roles_for_current_user')
    @patch('managesf.controllers.redmine.update_membership')
    @patch('managesf.controllers.redmine.edit_membership')
    @patch('managesf.controllers.redmine.user_is_administrator')
    @patch('managesf.controllers.redmine.get_role_id')
    @patch('managesf.controllers.redmine.get_user_id')
    def test_redmine_delete_user_from_projectgroups(
            self, get_user_id_mock, get_role_id_mock,
            user_is_administrator_mock, edit_membership_mock,
            update_membership_mock, get_project_roles_for_current_user_mock,
            get_project_membership_for_user_mock, delete_membership_mock):
        user2 = 'davis'
        user2_id = 102
        user2_mem_id = 2
        proj_id = 1
        mgr_role_id = 1
        dev_role_id = 2
        get_user_id_mock.return_value = user2_id
        user_is_administrator_mock.return_value = False
        get_role_id_mock.return_value = dev_role_id

        # If no membership for the user, then it should return None
        get_project_membership_for_user_mock.return_value = None
        self.assertEqual(
            None, redmine.delete_user_from_projectgroups('sf-demo', user2,
                                                         'dev-group'))
        mgr_role = {'name': 'Manager', 'id': mgr_role_id}
        dev_role = {'name': 'Developer', 'id': dev_role_id}
        membership = {'id': user2_mem_id,
                      'project': {'name': 'sf-demo', 'id': proj_id},
                      'user': {'name': 'david', 'id': user2_id},
                      'roles': [{'role': mgr_role},
                                {'role': dev_role}]}
        get_project_membership_for_user_mock.return_value = membership
        # 401 error, when Develper try to delete user from ptl group
        get_project_roles_for_current_user_mock.return_value = ['Developer']
        self.assertRaises(exc.HTTPUnauthorized,
                          redmine.delete_user_from_projectgroups,
                          'sf-demo', user2, 'ptl-group')

        # 401 error, when non-member try to delete user from any group
        get_project_roles_for_current_user_mock.return_value = []
        self.assertRaises(exc.HTTPUnauthorized,
                          redmine.delete_user_from_projectgroups,
                          'sf-demo', user2, 'core-group')
        self.assertRaises(exc.HTTPUnauthorized,
                          redmine.delete_user_from_projectgroups,
                          'sf-demo', user2, 'ptl-group')

        # Delete from all groups
        get_project_roles_for_current_user_mock.return_value = ['Manager']
        redmine.delete_user_from_projectgroups('sf-demo', user2, None)
        delete_membership_mock.assert_called_once_with(user2_mem_id)

        membership = {'id': user2_mem_id,
                      'project': {'name': 'sf-demo', 'id': proj_id},
                      'user': {'name': 'david', 'id': user2_id},
                      'roles': [{'name': 'Manager', 'id': mgr_role_id},
                                {'name': 'Developer', 'id': dev_role_id}]}
        get_project_membership_for_user_mock.return_value = membership
        redmine.delete_user_from_projectgroups('sf-demo', user2, 'core-group')
        update_membership_mock.assert_called_once_with(user2_mem_id,
                                                       [mgr_role_id])
        update_membership_mock.reset_mock()

        get_role_id_mock.return_value = mgr_role_id
        redmine.delete_user_from_projectgroups('sf-demo', user2, 'ptl-group')
        update_membership_mock.assert_called_once_with(user2_mem_id,
                                                       [dev_role_id])

    def test_redmine_get_project_membership_for_user(self):
        def fake_send_request(url, ret, method, **kwargs):
            self.assertIn('sf-demo', url)
            self.assertEqual(method, 'GET')
            self.assertEqual(ret, [200])
            data = {"memberships": [{'user': {'id': 101}}]}
            return FakeResponse(200, json.dumps(data))
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                m = redmine.get_project_membership_for_user('sf-demo', 101)
                self.assertEqual(m, {'user': {'id': 101}})

    @patch('managesf.controllers.redmine.get_project_membership_for_user')
    @patch('managesf.controllers.redmine.get_current_user_id')
    def test_redmine_get_project_roles_for_current_user(
            self, get_current_user_id_mock,
            get_project_membership_for_user_mock):
        get_current_user_id_mock.return_value = 101
        get_project_membership_for_user_mock.return_value = None
        # This call should return empty list
        roles = redmine.get_project_roles_for_current_user('sf-demo')
        self.assertEqual(roles, [])
        get_current_user_id_mock.assert_called_once_with()
        get_project_membership_for_user_mock.assert_called_once_with('sf-demo',
                                                                     101)

        m = {'roles': [{'name': 'Manager'}, {'name': 'Developer'}]}
        get_project_membership_for_user_mock.return_value = m
        # This call should return ['Manager', 'Developer']
        roles = redmine.get_project_roles_for_current_user('sf-demo')
        self.assertEqual(roles, ['Manager', 'Developer'])

    @patch('managesf.controllers.redmine.get_project_roles_for_current_user')
    def test_redmine_user_manages_project(
            self, get_project_roles_for_current_user_mock):
        get_project_roles_for_current_user_mock.return_value = []
        # This call should return False
        self.assertEqual(False, redmine.user_manages_project('sf-demo'))
        get_project_roles_for_current_user_mock.assert_called_once_with(
            'sf-demo')

        get_project_roles_for_current_user_mock.return_value = ['Manager']
        # This call should return True
        self.assertEqual(True, redmine.user_manages_project('sf-demo'))

    @patch('managesf.controllers.redmine.request')
    def test_redmine_user_is_administrator(self, request_mock):
        request_mock.remote_user = 'user2'
        # This call should return False
        self.assertEqual(False, redmine.user_is_administrator())

        request_mock.remote_user = 'user1'
        # This call should return True
        self.assertEqual(True, redmine.user_is_administrator())

    def test_redmine_delete_membership(self):
        def fake_send_request(url, ret, method, **kwargs):
            self.assertIn('1', url)
            self.assertEqual(method, 'DELETE')
            self.assertEqual(ret, [200])
            return FakeResponse(200)
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                redmine.delete_membership(1)

    @patch('managesf.controllers.redmine.user_manages_project')
    @patch('managesf.controllers.redmine.user_is_administrator')
    def test_redmine_delete_project(self, user_is_administrator_mock,
                                    user_manages_project_mock):
        def fake_send_request(url, ret, method, **kwargs):
            self.assertIn('sf-demo', url)
            self.assertEqual(method, 'DELETE')
            self.assertEqual(ret, [200])
            return FakeResponse(200)
        user_is_administrator_mock.return_value = False
        user_manages_project_mock.return_value = False
        self.assertRaises(exc.HTTPForbidden, redmine.delete_project, 'sf-demo')
        with patch('managesf.controllers.redmine.admin_auth_cookie'):
            with patch('managesf.controllers.redmine.send_request',
                       new_callable=lambda: fake_send_request):
                user_manages_project_mock.return_value = True
                redmine.delete_project('sf-demo')
