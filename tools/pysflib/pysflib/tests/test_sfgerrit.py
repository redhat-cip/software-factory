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
from mock import Mock
from requests.exceptions import HTTPError

from pysflib import sfgerrit


def raise_fake_exc(*args, **kwargs):
    e = HTTPError(response=Mock())
    e.response.status_code = 404
    raise e


class TestSFGerritRestAPI(TestCase):

    def test_init(self):
        ge = sfgerrit.SFGerritRestAPI('http://gerrit.tests.dom',
                                      auth_cookie='1234')
        self.assertEqual(ge.url, 'http://gerrit.tests.dom/r/a/')
        expected = {'verify': True,
                    'cookies': {'auth_pubtkt': '1234'},
                    'auth': None,
                    'headers': {'Accept-Encoding': 'gzip',
                                'Accept': 'application/json'}}
        self.assertDictEqual(ge.kwargs, expected)

    def test_verbs_calls(self):
        with patch('pygerrit.rest.requests.session'):
            with patch('pysflib.sfgerrit._decode_response'):
                ge = sfgerrit.SFGerritRestAPI('http://gerrit.tests.dom',
                                              auth_cookie='1234')
                ge.session.get = Mock()
                ge.session.put = Mock()
                ge.session.post = Mock()
                ge.session.delete = Mock()
                ge.get('projects/?')
                self.assertEqual(ge.session.get.call_count, 1)
                ge.put('projects/p1')
                self.assertEqual(ge.session.put.call_count, 1)
                ge.post('projects/p1')
                self.assertEqual(ge.session.post.call_count, 1)
                ge.delete('projects/p1')
                self.assertEqual(ge.session.delete.call_count, 1)


class TestGerritUtils(TestCase):

    @classmethod
    def setupClass(cls):
        cls.ge = sfgerrit.GerritUtils('http://gerrit.tests.dom',
                                      auth_cookie='1234')

    def test_manage_errors(self):
        fake_exc = HTTPError(response=Mock())
        fake_exc.response.status_code = 404
        self.assertFalse(self.ge._manage_errors(fake_exc))
        fake_exc.response.status_code = 409
        self.assertFalse(self.ge._manage_errors(fake_exc))

    def test_project_exists(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get'):
            self.assertTrue(self.ge.project_exists('p1'))
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.project_exists('p1'))

    def test_create_project(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.put'):
            self.assertEqual(self.ge.create_project('p1', 'desc', 'p1-ptl'),
                             None)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.put',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.create_project('p1', 'desc', 'p1-ptl'))

    def test_delete_project(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.delete'):
            self.assertEqual(self.ge.delete_project('p1'), None)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.delete',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.delete_project('p1'))

    def test_get_project(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = 'project'
            self.assertEqual(self.ge.get_project('p1'), 'project')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_project('p1'))

    def test_get_projects(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'a': None, 'b': None}
            self.assertListEqual(self.ge.get_projects(), ['a', 'b'])

    def test_get_project_owner(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'p1': {'local': {'refs/*':
                                     {'permissions': {'owner': {'rules':
                                      {'a': None, 'b': None}}}}}}}
            self.assertEqual(self.ge.get_project_owner('p1'), 'a')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_project_owner('p1'))
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'p1': {'local': {'refs/*':
                                     {'permissions': {'owner': None}}}}}
            self.assertEqual(self.ge.get_project_owner('p1'), None)

    def test_get_account(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = 'account'
            self.assertEqual(self.ge.get_account('user1'), 'account')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_account('user1'))

    def test_get_my_groups_id(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = [{'id': 1}, {'id': 2}]
            self.assertListEqual(self.ge.get_my_groups_id(), [1, 2])
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_my_groups_id())

    def test_groups_exists(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = ['p1-ptl', 'p2-ptl']
            self.assertTrue(self.ge.group_exists('p2-ptl'))

    def test_create_group(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.put'):
            self.assertEqual(self.ge.create_group('p1-ptl', 'desc'), None)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.put',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.create_group('p1-ptl', 'desc'))

    def test_get_group_id(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'id': 1}
            self.assertEqual(self.ge.get_group_id('p1-ptl'), 1)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_group_id('p1-ptl'))

    def test_get_group_member_id(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = [{'_account_id': 1, 'username': 'user1'}]
            self.assertEqual(self.ge.get_group_member_id('p1-ptl', 'user1'), 1)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_group_member_id('p1-ptl', 'user1'))

    def test_get_group_owner(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'owner': 'user1'}
            self.assertEqual(self.ge.get_group_owner('p1-ptl'), 'user1')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_group_owner('p1-ptl'))

    def test_member_in_group(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'username': 'user1'}
            self.assertTrue(self.ge.member_in_group('user1', 'p1-ptl'))
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.member_in_group('user1', 'p1-ptl'))

    def test_add_group_member(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post'):
            self.assertEqual(self.ge.add_group_member('user1', 'p1-ptl'), None)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.add_group_member('user1', 'p1-ptl'))

    def test_delete_group_member(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.delete'):
            self.assertEqual(self.ge.delete_group_member('p1-ptl', 'user1'),
                             None)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.delete',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.delete_group_member('p1-ptl', 'user1'))

    def test_add_pubkey(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post') as p:
            p.return_value = {'seq': 1}
            self.assertEqual(self.ge.add_pubkey('rsa ...'), 1)

    def test_del_pubkey(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.delete'):
            self.assertEqual(self.ge.del_pubkey(1), None)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.delete',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.del_pubkey(1))

    def test_submit_change_note(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post'):
            self.assertEqual(
                self.ge.submit_change_note('1', '1', 'Verified', 2), None)
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post',
                   side_effect=raise_fake_exc):
            self.assertFalse(
                self.ge.submit_change_note('1', '1', 'Verified', 2))

    def test_submit_patch(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post') as p:
            p.return_value = {'status': 'MERGED'}
            self.assertEqual(self.ge.submit_patch('1', '1'), True)
            p.return_value = {'status': 'OPEN'}
            self.assertFalse(self.ge.submit_patch('1', '1'))
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.submit_patch('1', '1'))

    def test_get_reviewer_approvals(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = [{'approvals': 'app'}]
            self.assertEqual(
                self.ge.get_reviewer_approvals('1', 'jenkins'), 'app')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_reviewer_approvals('1', 'jenkins'))

    def test_get_reviewers(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = [{'username': 'user1'}]
            self.assertListEqual(self.ge.get_reviewers('1'), ['user1'])
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_reviewers('1'))

    def test_get_my_changes_for_project(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = [{'change_id': '123'}]
            self.assertListEqual(
                self.ge.get_my_changes_for_project('p1'), ['123'])
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_my_changes_for_project('p1'))

    def test_get_change(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = '123'
            self.assertEqual(self.ge.get_change('p1', 'master', '123'), '123')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_change('p1', 'master', '123'))

    def test_get_change_last_patchset(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = 'b'
            self.assertEqual(self.ge.get_change_last_patchset('123'), 'b')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_change_last_patchset('123'))

    def test_get_labels_list_for_change(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'labels': 'b'}
            self.assertEqual(self.ge.get_labels_list_for_change('123'), 'b')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.get_labels_list_for_change('123'))

    def test_list_plugins(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.get') as g:
            g.return_value = {'delete-project': '', 'gravatar': ''}
            self.assertListEqual(
                sorted(self.ge.list_plugins()), ['delete-project', 'gravatar'])

    def test_e_d_plugin(self):
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post') as p:
            p.return_value = 'plugin'
            self.assertEqual(
                self.ge.e_d_plugin('gravatar', 'enable'), 'plugin')
        with patch('pysflib.sfgerrit.SFGerritRestAPI.post',
                   side_effect=raise_fake_exc):
            self.assertFalse(self.ge.e_d_plugin('gravatar', 'enable'))
