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


import os

from unittest import TestCase
from webtest import TestApp
from pecan import load_app
from contextlib import nested
from mock import patch

from managesf.tests import dummy_conf


def raiseexc(*args, **kwargs):
    raise Exception('FakeExcMsg')


class FunctionalTest(TestCase):
    def setUp(self):
        c = dummy_conf()
        config = {'gerrit': c.gerrit,
                  'app': c.app,
                  'admin': c.admin}
        # deactivate loggin that polute test output
        # even nologcapture option of nose effetcs
        # 'logging': c.logging}
        self.app = TestApp(load_app(config))

    def tearDown(self):
        pass


class TestManageSFAppProjectController(FunctionalTest):
    def test_project_get(self):
        # Project GET is not supported right now
        response = self.app.get('/project', status="*")
        self.assertEqual(response.status_int, 501)

    def test_project_put(self):
        # Create a project with no name
        response = self.app.put('/project/', status="*")
        self.assertEqual(response.status_int, 400)
        # Create a project with name
        ctx = [patch('managesf.controllers.gerrit.init_project'),
               patch('managesf.controllers.redmine.init_project')]
        with nested(*ctx) as (gip, rip):
            response = self.app.put('/project/p1', status="*")
            self.assertTupleEqual(('p1', {}), gip.mock_calls[0][1])
            self.assertTupleEqual(('p1', {}), rip.mock_calls[0][1])
            self.assertEqual(response.status_int, 201)
            self.assertEqual(response.body, 'Project p1 has been created.')
        # Create a project with name - an error occurs
        ctx = [patch('managesf.controllers.gerrit.init_project'),
               patch('managesf.controllers.redmine.init_project',
               side_effect=raiseexc)]
        with nested(*ctx) as (gip, rip):
            response = self.app.put('/project/p1', status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')

    def test_project_delete(self):
        # Delete a project with no name
        response = self.app.delete('/project/', status="*")
        self.assertEqual(response.status_int, 400)
        # Delete a project with name
        ctx = [patch('managesf.controllers.gerrit.delete_project'),
               patch('managesf.controllers.redmine.delete_project')]
        with nested(*ctx) as (gdp, rdp):
            response = self.app.delete('/project/p1', status="*")
            self.assertTupleEqual(('p1',), gdp.mock_calls[0][1])
            self.assertTupleEqual(('p1',), rdp.mock_calls[0][1])
            self.assertEqual(response.status_int, 200)
            self.assertEqual(response.body, 'Project p1 has been deleted.')
        # Delete a project with name - an error occurs
        ctx = [patch('managesf.controllers.gerrit.delete_project'),
               patch('managesf.controllers.redmine.delete_project',
               side_effect=raiseexc)]
        with nested(*ctx) as (gip, rip):
            response = self.app.delete('/project/p1', status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')


class TestManageSFAppRestoreController(FunctionalTest):
    def tearDown(self):
        if os.path.isfile('/tmp/sf_backup.tar.gz'):
            os.unlink('/tmp/sf_backup.tar.gz')

    def test_restore_post(self):
        files = [('file', 'useless', 'backup content')]
        # retore a provided backup
        with patch('managesf.controllers.backup.backup_restore') as br:
            response = self.app.post('/restore', status="*",
                                     upload_files=files)
            self.assertTrue(os.path.isfile('/tmp/sf_backup.tar.gz'))
            self.assertTrue(br.called)
            self.assertEqual(response.status_int, 204)
        # retore a provided backup - an error occurs
        with patch('managesf.controllers.backup.backup_restore',
                   side_effect=raiseexc) as br:
            response = self.app.post('/restore', status="*",
                                     upload_files=files)
            self.assertTrue(os.path.isfile('/tmp/sf_backup.tar.gz'))
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')


class TestManageSFAppBackupController(FunctionalTest):
    def tearDown(self):
        if os.path.isfile('/tmp/sf_backup.tar.gz'):
            os.unlink('/tmp/sf_backup.tar.gz')

    def test_backup_get(self):
        with patch('managesf.controllers.backup.backup_get') as bg:
            file('/tmp/sf_backup.tar.gz', 'w').write('backup content')
            response = self.app.get('/backup', status="*")
            self.assertTrue(bg.called)
            self.assertEqual(response.body, 'backup content')
            os.unlink('/tmp/sf_backup.tar.gz')
            response = self.app.get('/backup', status="*")
            self.assertEqual(response.status_int, 404)
        with patch('managesf.controllers.backup.backup_get',
                   side_effect=raiseexc):
            response = self.app.get('/backup', status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')

    def test_backup_post(self):
        with patch('managesf.controllers.backup.backup_start') as bs:
            response = self.app.post('/backup', status="*")
            self.assertTrue(bs.called)
            self.assertEqual(response.status_int, 204)
        with patch('managesf.controllers.backup.backup_start',
                   side_effect=raiseexc):
            response = self.app.post('/backup', status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')


class TestManageSFAppMembershipController(FunctionalTest):
    def test_get(self):
        # Membership GET is not supported right now
        response = self.app.get('/project/membership', status="*")
        self.assertEqual(response.status_int, 501)

    def test_put(self):
        response = self.app.put_json('/project/membership/', {}, status="*")
        self.assertEqual(response.status_int, 400)
        response = self.app.put_json('/project/membership/p1/', {}, status="*")
        self.assertEqual(response.status_int, 400)
        response = self.app.put_json('/project/membership/p1/john', {},
                                     status="*")
        self.assertEqual(response.status_int, 400)
        ctx = [patch('managesf.controllers.gerrit.add_user_to_projectgroups'),
               patch('managesf.controllers.redmine.add_user_to_projectgroups')]
        with nested(*ctx) as (gaupg, raupg):
            response = self.app.put_json(
                '/project/membership/p1/john',
                {'groups': ['ptl-group', 'core-group']},
                status="*")
            self.assertEqual(response.status_int, 201)
            self.assertEqual(
                "User john has been added in group(s): ptl-group, "
                "core-group for project p1",
                response.body)
        ctx = [patch('managesf.controllers.gerrit.add_user_to_projectgroups'),
               patch('managesf.controllers.redmine.add_user_to_projectgroups',
               side_effect=raiseexc)]
        with nested(*ctx) as (gaupg, raupg):
            response = self.app.put_json(
                '/project/membership/p1/john',
                {'groups': ['ptl-group', 'core-group']},
                status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')

    def test_delete(self):
        response = self.app.delete('/project/membership/', status="*")
        self.assertEqual(response.status_int, 400)
        response = self.app.delete('/project/membership/p1/', status="*")
        self.assertEqual(response.status_int, 400)
        ctx = [
            patch(
                'managesf.controllers.gerrit.delete_user_from_projectgroups'),
            patch(
                'managesf.controllers.redmine.delete_user_from_projectgroups')]
        with nested(*ctx) as (gdupg, rdupg):
            response = self.app.delete(
                '/project/membership/p1/john',
                status="*")
            self.assertEqual(response.status_int, 200)
            self.assertEqual(
                "User john has been deleted from all groups for project p1.",
                response.body)
            response = self.app.delete(
                '/project/membership/p1/john/core-group',
                status="*")
            self.assertEqual(response.status_int, 200)
            self.assertEqual(
                "User john has been deleted from group core-group "
                "for project p1.",
                response.body)
        ctx = [
            patch(
                'managesf.controllers.gerrit.delete_user_from_projectgroups'),
            patch(
                'managesf.controllers.redmine.delete_user_from_projectgroups',
                side_effect=raiseexc)]
        with nested(*ctx) as (gdupg, rdupg):
            response = self.app.delete(
                '/project/membership/p1/john',
                status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')


class TestManageSFAppReplicationController(FunctionalTest):
    def test_put(self):
        response = self.app.put_json('/replication/', {}, status="*")
        self.assertEqual(response.status_int, 400)
        response = self.app.put_json('/replication/repl', {}, status="*")
        self.assertEqual(response.status_int, 400)
        with patch('managesf.controllers.gerrit.replication_apply_config'):
            response = self.app.put_json(
                '/replication/repl', {'value': 'val'}, status="*")
            self.assertEqual(response.status_int, 204)
        with patch('managesf.controllers.gerrit.replication_apply_config',
                   side_effect=raiseexc):
            response = self.app.put_json(
                '/replication/repl', {'value': 'val'}, status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')

    def test_delete(self):
        response = self.app.delete('/replication/', status="*")
        self.assertEqual(response.status_int, 400)
        with patch('managesf.controllers.gerrit.replication_apply_config'):
            response = self.app.delete(
                '/replication/repl', status="*")
            self.assertEqual(response.status_int, 204)
        with patch('managesf.controllers.gerrit.replication_apply_config',
                   side_effect=raiseexc):
            response = self.app.delete(
                '/replication/repl', status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')

    def test_get(self):
        response = self.app.get('/replication/', status="*")
        self.assertEqual(response.status_int, 400)
        with patch('managesf.controllers.gerrit.replication_get_config') \
                as rgc:
            rgc.return_value = 'ret val'
            response = self.app.get(
                '/replication/repl/', status="*")
            self.assertEqual(response.status_int, 200)
            self.assertEqual(response.body, 'ret val')
        with patch('managesf.controllers.gerrit.replication_get_config',
                   side_effect=raiseexc):
            response = self.app.get(
                '/replication/repl/', status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')

    def test_post(self):
        with patch('managesf.controllers.gerrit.replication_trigger'):
            response = self.app.post_json(
                '/replication/',
                {},
                status="*")
            self.assertEqual(response.status_int, 204)
            print response.body
        with patch('managesf.controllers.gerrit.replication_trigger',
                   side_effect=raiseexc):
            response = self.app.post_json(
                '/replication/', status="*")
            self.assertEqual(response.status_int, 500)
            self.assertEqual(response.body,
                             'Unable to process your request, failed '
                             'with unhandled error (server side): FakeExcMsg')
