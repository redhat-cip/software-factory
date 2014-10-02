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
from contextlib import nested
from pecan.core import exc
from subprocess import Popen, PIPE

import os
import tempfile

from managesf.controllers import gerrit
from managesf.tests import dummy_conf

repl_content = """[repl]
    projects = p1
    url = gerrit@$mysqlh:/home/gerrit/site_path/git/p1.git
    push = +refs/heads/*:refs/heads/*
"""

repl_content_buggy = """[repl]
    projects = p1
    gerrit@$mysqlh:/home/gerrit/site_path/git/p1.git
    push = +refs/heads/*:refs/heads/*
"""


def fake_replication_ssh_run_cmd(cmd):
    cmd = ['git', 'config', '-f',
           dummy_conf().gerrit['replication_config_path'], '-l']
    p1 = Popen(cmd, stdout=PIPE)
    out, err = p1.communicate()
    return out, err, p1.returncode


def fake_get_group_id(cls, name):
    if name == 'Administrators':
        return 0
    if name == 'p1-ptl':
        return 1
    if name == 'p1-core':
        return 2
    if name == 'p1-dev':
        return 3
    if name == 'Non-Interactive%20Users':
        return 4


class FakeResponse():
    def __init__(self, code, content=None, text=None):
        self.status_code = code
        self.content = content
        self.text = text


class TestGerritController(TestCase):
    @classmethod
    def setupClass(cls):
        cls.conf = dummy_conf()
        gerrit.conf = cls.conf

    def test_get_projects_by_user(self):
        all_projects = ('p1', 'p2', 'p3')
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.GerritUtils.get_projects'),
               patch('managesf.controllers.gerrit.user_is_administrator'),
               patch('managesf.controllers.gerrit.user_owns_project')]
        with nested(*ctx) as (gc, gp, uia, uop):
            gp.return_value = all_projects
            uia.return_value = True
            projects = gerrit.get_projects_by_user()
            self.assertTupleEqual(projects, all_projects)
            uia.return_value = False
            uop.return_value = True
            projects = gerrit.get_projects_by_user()
            self.assertTupleEqual(tuple(projects), all_projects)
            uop.side_effect = [True, False, False]
            projects = gerrit.get_projects_by_user()
            self.assertTupleEqual(tuple(projects), ('p1',))

    def test_create_group(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.GerritUtils.create_group'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.add_group_member')]
        with nested(*ctx) as (gc, cg, agm):
            m = Mock()
            m.remote_user = 'user1'
            gerrit.request = m
            gerrit.create_group('p1-ptl', 'desc')
            self.assertTupleEqual(('p1-ptl', 'desc'), cg.mock_calls[0][1])
            self.assertTupleEqual(('user1', 'p1-ptl'), agm.mock_calls[0][1])

    def test_get_my_groups(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.get_my_groups_id')]
        with nested(*ctx) as (gc, gmgi):
            m = Mock()
            m.cookies = {'auth_pubtkt': '1234'}
            gerrit.request = m
            gerrit.get_my_groups()
            self.assertTrue(gmgi.called)

    def test_user_owns_project(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.get_my_groups'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.'
                   'get_project_owner')]
        with nested(*ctx) as (gc, gmg, gpo):
            gmg.return_value = ['p1-ptl']
            gpo.return_value = 'p1-ptl'
            self.assertTrue(gerrit.user_owns_project('p1'))

    def test_user_is_administrator(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.get_my_groups'),
               patch('managesf.controllers.gerrit.GerritUtils.get_group_id',
                     new_callable=lambda: fake_get_group_id)]
        with nested(*ctx) as (gc, gmg, ggi):
            gmg.return_value = [0, 1]
            self.assertTrue(gerrit.user_is_administrator())

    def test_get_group_name(self):
        self.assertEqual('p1-core', gerrit.get_core_group_name('p1'))
        self.assertEqual('p1-ptl', gerrit.get_ptl_group_name('p1'))
        self.assertEqual('p1-dev', gerrit.get_dev_group_name('p1'))

    def test_init_project(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.init_git_repo'),
               patch('managesf.controllers.gerrit.create_group'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.add_group_member'),
               patch('managesf.controllers.gerrit.GerritUtils.create_project'),
               patch('managesf.controllers.gerrit.request'),
               ]
        with nested(*ctx) as (gc, igr, cg, autg, cp, r):
            data = {'description': 'the desc'}
            gerrit.init_project('p1', data)
            self.assertEqual(2, len(cg.mock_calls))
            call1, call2 = cg.mock_calls
            self.assertTupleEqual(('p1-core',
                                   'Core developers for project p1'),
                                  call1[1])
            self.assertTupleEqual(('p1-ptl',
                                   'Project team lead for project p1'),
                                  call2[1])
            self.assertEqual(1, len(cp.mock_calls))
            self.assertTupleEqual(('p1', 'the desc', ['p1-ptl']),
                                  cp.mock_calls[0][1])
            self.assertFalse(autg.called)
        with nested(*ctx) as (gc, igr, cg, autg, cp, r):
            data = {'description': 'the desc', 'private': True}
            gerrit.init_project('p1', data)
            self.assertEqual(3, len(cg.mock_calls))
            call1, call2, call3 = cg.mock_calls
            self.assertTupleEqual(('p1-core',
                                   'Core developers for project p1'),
                                  call1[1])
            self.assertTupleEqual(('p1-ptl',
                                   'Project team lead for project p1'),
                                  call2[1])
            self.assertTupleEqual(('p1-dev',
                                   'Developers for project p1'),
                                  call3[1])
            self.assertEqual(1, len(cp.mock_calls))
            self.assertTupleEqual(('p1', 'the desc', ['p1-ptl']),
                                  cp.mock_calls[0][1])
            self.assertFalse(autg.called)
        with nested(*ctx) as (gc, igr, cg, autg, cp, r):
            data = {'description': 'the desc', 'private': True,
                    'upstream': 'git://tests.net/git/blah.git',
                    'core-group-members': ['u1', 'u2'],
                    'ptl-group-members': ['u3', 'u4'],
                    'dev-group-members': ['u5', 'u6'],
                    }
            gerrit.init_project('p1', data)
            self.assertEqual(3, len(cg.mock_calls))
            self.assertEqual(6, len(autg.mock_calls))
            self.assertEqual(1, len(cp.mock_calls))
            self.assertEqual(1, len(igr.mock_calls))
            self.assertTupleEqual(('p1', 'the desc', ['p1-ptl']),
                                  cp.mock_calls[0][1])
            self.assertTupleEqual(('p1', 'the desc',
                                   'git://tests.net/git/blah.git', True),
                                  igr.mock_calls[0][1])

    def test_add_user_to_projectgroups(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.get_my_groups'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.add_group_member'),
               patch('managesf.controllers.gerrit.GerritUtils.group_exists'),
               patch('managesf.controllers.gerrit.GerritUtils.get_group_id',
                     new_callable=lambda: fake_get_group_id)]
        with nested(*ctx) as (gc, gg, autg, cige, ggi):
            gg.return_value = [1]
            cige.return_value = True
            gerrit.add_user_to_projectgroups(
                'p1', 'john', ['ptl-group', 'core-group', 'dev-group'])
            self.assertEqual(3, len(autg.mock_calls))
            call1, call2, call3 = autg.mock_calls
            self.assertTupleEqual(('john', 'p1-ptl'), call1[1])
            self.assertTupleEqual(('john', 'p1-core'), call2[1])
            self.assertTupleEqual(('john', 'p1-dev'), call3[1])
        with nested(*ctx) as (gc, gg, autg, cige, ggi):
            gg.return_value = [2]
            cige.return_value = True
            self.assertRaises(
                exc.HTTPUnauthorized, lambda:
                    gerrit.add_user_to_projectgroups(
                        'p1', 'john',
                        ['ptl-group', 'core-group', 'dev-group']))
            self.assertEqual(0, len(autg.mock_calls))
        with nested(*ctx) as (gc, gg, autg, cige, ggi):
            gg.return_value = [2]
            cige.return_value = True
            gerrit.add_user_to_projectgroups(
                'p1', 'john', ['core-group', 'dev-group'])
            self.assertEqual(2, len(autg.mock_calls))
            call1, call2 = autg.mock_calls
            self.assertTupleEqual(('john', 'p1-core'), call1[1])
            self.assertTupleEqual(('john', 'p1-dev'), call2[1])
        with nested(*ctx) as (gc, gg, autg, cige, ggi):
            gg.return_value = [3]
            cige.return_value = True
            self.assertRaises(
                exc.HTTPUnauthorized, lambda:
                    gerrit.add_user_to_projectgroups(
                        'p1', 'john',
                        ['core-group', 'dev-group']))
            self.assertEqual(0, len(autg.mock_calls))
        with nested(*ctx) as (gc, gg, autg, cige, ggi):
            gg.return_value = [3]
            cige.return_value = True
            gerrit.add_user_to_projectgroups('p1', 'john', ['dev-group'])
            self.assertEqual(1, len(autg.mock_calls))
            call1 = autg.mock_calls[0]
            self.assertTupleEqual(('john', 'p1-dev'), call1[1])

    def test_delete_user_from_projectgroups(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.get_my_groups'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.'
                   'delete_group_member'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.'
                   'get_group_member_id'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.group_exists'),
               patch(
                   'managesf.controllers.gerrit.GerritUtils.get_group_id',
                   new_callable=lambda: fake_get_group_id)]
        with nested(*ctx) as (gc, gg, dgm, ggmid, cige, ggi):
            gg.return_value = [1]
            ggmid.return_value = 42
            cige.return_value = True
            gerrit.delete_user_from_projectgroups('p1', 'john', [])
            self.assertEqual(3, len(dgm.mock_calls))
            call1, call2, call3 = dgm.mock_calls
            self.assertTupleEqual((3, 42), call1[1])
            self.assertTupleEqual((1, 42), call2[1])
            self.assertTupleEqual((2, 42), call3[1])
        with nested(*ctx) as (gc, gg, dgm, ggmid, cige, ggi):
            gg.return_value = [1]
            ggmid.return_value = 42
            cige.return_value = True
            gerrit.delete_user_from_projectgroups('p1', 'john', 'dev-group')
            self.assertEqual(1, len(dgm.mock_calls))
            call1 = dgm.mock_calls[0]
            self.assertTupleEqual((3, 42), call1[1])
        with nested(*ctx) as (gc, gg, dgm, ggmid, cige, ggi):
            gg.return_value = [3]
            ggmid.return_value = 42
            cige.return_value = True
            self.assertRaises(
                exc.HTTPUnauthorized, lambda:
                    gerrit.delete_user_from_projectgroups(
                        'p1', 'john', 'ptl-group'))
            self.assertEqual(0, len(dgm.mock_calls))

    def test_delete_project(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.user_owns_project'),
               patch('managesf.controllers.gerrit.user_is_administrator'),
               patch('managesf.controllers.gerrit.GerritUtils.delete_project'),
               patch(
               'managesf.controllers.gerrit.CustomGerritClient.deleteGroup'),
               patch('managesf.controllers.gerrit.gerrit.Gerrit._ssh')]
        with nested(*ctx) as (gc, uop, uia, dp, dg, ssh):
            ssh.return_value = ("", "")
            uop.return_value = False
            uia.return_value = False
            self.assertRaises(
                exc.HTTPUnauthorized, lambda:
                gerrit.delete_project("p1"))
        with nested(*ctx) as (gc, uop, uia, dp, dg, ssh):
            ssh.return_value = ("", "")
            uop.return_value = True
            uia.return_value = False
            gerrit.delete_project("p1")
            self.assertEqual(3, len(dg.mock_calls))
            self.assertTrue(dp.called)
        with nested(*ctx) as (gc, uop, uia, dp, dg, ssh):
            ssh.return_value = ("", "")
            uop.return_value = False
            uia.return_value = True
            gerrit.delete_project("p1")
            self.assertEqual(3, len(dg.mock_calls))
            self.assertTrue(dp.called)

    def test_init_git_repo(self):
        ctx = [patch('managesf.controllers.gerrit.get_cookie'),
               patch('managesf.controllers.gerrit.GerritRepo.clone'),
               patch('managesf.controllers.gerrit.GerritRepo.push_config'),
               patch(
               'managesf.controllers.gerrit.GerritRepo.push_master_from_git_remote'),  # noqa
               patch('managesf.controllers.gerrit.GerritRepo.push_master'),
               patch('managesf.controllers.gerrit.GerritUtils.get_group_id',
                     new_callable=lambda: fake_get_group_id)]
        with nested(*ctx) as (gc, c, pc, pmfgr, pm, ggi):
            gerrit.init_git_repo("p1", "the desc",
                                 "git://tests.dom/git/oldp1.git", True)
            arg_paths = pc.mock_calls[0][1][0]
            self.assertTrue(arg_paths['groups'])
            self.assertTrue(arg_paths['project.config'])
            self.assertTrue(c.called)
            self.assertTrue(pmfgr.called)
            self.assertTrue(pm.called)

    def test_replication_ssh_run_cmd(self):
        def fake_popen(*args, **kwargs):
            return FakePopen()

        class FakePopen():
            def __init__(self):
                self.returncode = 0

            def communicate(self):
                return "", ""
        with patch('managesf.controllers.gerrit.Popen',
                   new_callable=lambda: fake_popen):
            out, err, code = gerrit.replication_ssh_run_cmd(["ls"])

    def test_replication_read_config(self):
        with patch(
                'managesf.controllers.gerrit.replication_ssh_run_cmd',
                new_callable=lambda: fake_replication_ssh_run_cmd):
            exp_ret = {'repl': {
                'url': ['gerrit@$mysqlh:/home/gerrit/site_path/git/p1.git'],
                'push': ['+refs/heads/*:refs/heads/*'], 'projects': ['p1']}}
            file(self.conf.gerrit['replication_config_path'], 'w').\
                write(repl_content)
            config = gerrit.replication_read_config()
            self.assertDictEqual(exp_ret, config)
            file(self.conf.gerrit['replication_config_path'], 'w').\
                write(repl_content_buggy)
            self.assertRaises(exc.HTTPInternalServerError,
                              lambda: gerrit.replication_read_config())

    def test_replication_validate(self):
        with patch(
                'managesf.controllers.gerrit.replication_ssh_run_cmd',
                new_callable=lambda: fake_replication_ssh_run_cmd):
            file(self.conf.gerrit['replication_config_path'], 'w').\
                write(repl_content)
            config = gerrit.replication_read_config()
            gerrit.replication_validate("p1", config, "repl", "push")
            # TODO: seems there is a problem for the test below ?
            gerrit.replication_validate("p1", config, "sec2", "projects")
            self.assertRaises(exc.HTTPForbidden, lambda:
                              gerrit.replication_validate(
                                  "p2", config, "repl", "projects"))
            self.assertRaises(exc.HTTPClientError, lambda:
                              gerrit.replication_validate(
                                  "p1", config, "repl", "blah"))

    def test_replication_apply_config(self):
        ctx = [patch('managesf.controllers.gerrit.get_projects_by_user'),
               patch('managesf.controllers.gerrit.replication_ssh_run_cmd',
                     new_callable=lambda: fake_replication_ssh_run_cmd),

               patch('managesf.controllers.gerrit.CustomGerritClient.reload_replication_plugin')]  # noqa
        with nested(*ctx) as (gpbu, rsrc, rrp):
            file(self.conf.gerrit['replication_config_path'], 'w').\
                write(repl_content)
            gpbu.return_value = ('p1', 'p2')
            gerrit.replication_apply_config('repl')
            self.assertTrue(rrp.called)
            gpbu.return_value = ('p2', 'p3')
            self.assertRaises(exc.HTTPForbidden, lambda:
                              gerrit.replication_apply_config('repl'))

    def test_replication_get_config(self):
        ctx = [patch('managesf.controllers.gerrit.get_projects_by_user'),
               patch('managesf.controllers.gerrit.replication_ssh_run_cmd',
                     new_callable=lambda: fake_replication_ssh_run_cmd)]
        with nested(*ctx) as (gpbu, rsrc):
            file(self.conf.gerrit['replication_config_path'], 'w').\
                write(repl_content)
            gpbu.return_value = ('p1', 'p2')
            config = gerrit.replication_get_config()
            self.assertTrue(config)
            config = gerrit.replication_get_config('repl')
            self.assertTrue(config)
            # TODO: is this real behaviour we want for the tests below ?
            config = gerrit.replication_get_config('notexist')
            self.assertTrue(config)
            gpbu.return_value = ('p2', 'p3')
            config = gerrit.replication_get_config('notexist')
            self.assertFalse(config)

    def test_replication_trigger(self):
        data = {'wait': True,
                'url': 'gerrit@$mysqlh:/home/gerrit/site_path/git/p1.git',
                'project': 'p1'}
        ctx = [patch('managesf.controllers.gerrit.get_projects_by_user'),
               patch('managesf.controllers.gerrit.CustomGerritClient.trigger_replication'),  # noqa
               patch('managesf.controllers.gerrit.replication_ssh_run_cmd',
                     new_callable=lambda: fake_replication_ssh_run_cmd)]
        with nested(*ctx) as (gpbu, tr, rsrc):
            file(self.conf.gerrit['replication_config_path'], 'w').\
                write(repl_content)
            gpbu.return_value = ('p1', 'p2')
            gerrit.replication_trigger(data)
            # TODO: wait should be in the command ?
            self.assertEqual(
                ' replication start --url gerrit@$mysqlh:/home/gerrit/site_path/git/p1.git',  # noqa
                tr.mock_calls[0][1][0])


class TestGerritRepo(TestCase):
    @classmethod
    def setupClass(cls):
        cls.conf = dummy_conf()
        gerrit.conf = cls.conf

    def test_init(self):
        gr = gerrit.GerritRepo('p1')
        self.assertTrue(gr.infos['localcopy_path'].endswith('p1'))
        self.assertTrue(os.path.isfile(gr.env['GIT_SSH']))
        self.assertTrue(gr.env['GIT_COMMITTER_NAME'])
        self.assertTrue(gr.env['GIT_COMMITTER_EMAIL'])

    def test_exec(self):
        gr = gerrit.GerritRepo('p1')
        p = tempfile.mkdtemp()
        gr._exec('touch f', p)
        self.assertTrue(os.path.isfile(os.path.join(p, 'f')))

    def test_clone(self):
        with patch('managesf.controllers.gerrit.GerritRepo._exec') as ex:
            gr = gerrit.GerritRepo('p1')
            gr.clone()
            self.assertEqual(
                'git clone ssh://user1@gerrit.test.dom:2929/p1 %s' %
                gr.infos['localcopy_path'],
                ex.mock_calls[0][1][0])

    def test_add_file(self):
        with patch('managesf.controllers.gerrit.GerritRepo._exec') as ex:
            gr = gerrit.GerritRepo('p1')
            gr.add_file('thefile', 'thecontent')
            p = os.path.join(gr.infos['localcopy_path'], 'thefile')
            self.assertTrue(os.path.isfile(p))
            self.assertEqual('thecontent', file(p).read())
            self.assertEqual('git add thefile', ex.mock_calls[0][1][0])
            self.assertEqual(gr.infos['localcopy_path'],
                             ex.mock_calls[0][2]['cwd'])

    def test_push_config(self):
        with patch('managesf.controllers.gerrit.GerritRepo._exec') as ex:
            with patch('managesf.controllers.gerrit.GerritRepo.add_file') \
                    as af:
                gr = gerrit.GerritRepo('p1')
                gr.push_config({'f1': 'contentf1', 'f2': 'contentf2'})
                self.assertEqual(2, len(af.mock_calls))
                self.assertEqual(4, len(ex.mock_calls))

    def test_push_master(self):
        with patch('managesf.controllers.gerrit.GerritRepo._exec') as ex:
            with patch('managesf.controllers.gerrit.GerritRepo.add_file') \
                    as af:
                gr = gerrit.GerritRepo('p1')
                gr.push_master({'f1': 'contentf1', 'f2': 'contentf2'})
                self.assertEqual(2, len(af.mock_calls))
                self.assertEqual(3, len(ex.mock_calls))

    def test_push_master_from_git_remote(self):
        with patch('managesf.controllers.gerrit.GerritRepo._exec') as ex:
            gr = gerrit.GerritRepo('p1')
            gr.push_master_from_git_remote('git://tests.dom/git/oldp1.git')
            self.assertEqual(5, len(ex.mock_calls))


class TestCustomGerritClient(TestCase):
    def test_reload_replication_plugin(self):
        with patch('managesf.controllers.gerrit.gerrit.Gerrit._ssh') as ssh:
            cgc = gerrit.CustomGerritClient('gerrit.tests.dom', 'admin')
            ssh.return_value = ("", "")
            cgc.reload_replication_plugin()
            self.assertTrue(ssh.called)

    def test_trigger_replication(self):
        with patch('managesf.controllers.gerrit.gerrit.Gerrit._ssh') as ssh:
            cgc = gerrit.CustomGerritClient('gerrit.tests.dom', 'admin')
            ssh.return_value = ("", "")
            cgc.trigger_replication("cmd")
            self.assertTrue(ssh.called)

    def test_deleteGroup(self):
        with patch('managesf.controllers.gerrit.gerrit.Gerrit._ssh') as ssh:
            cgc = gerrit.CustomGerritClient('gerrit.tests.dom', 'admin')
            ssh.return_value = ("", "")
            cgc.deleteGroup("p1-dev")
            self.assertEqual(6, len(ssh.mock_calls))
