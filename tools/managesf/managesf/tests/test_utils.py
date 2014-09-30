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
from managesf.controllers import utils
from managesf.tests import dummy_conf

import json


class FakeResponse():
    def __init__(self, code, content=None, text=None, cookies=None):
        self.status_code = code
        self.content = content
        self.text = text
        self.cookies = cookies

    def json(self):
        return json.loads(self.content)


class TestUtils(TestCase):
    @classmethod
    def setupClass(cls):
        cls.conf = dummy_conf()
        utils.conf = cls.conf


class TestRemoteUser(TestCase):
    @classmethod
    def setupClass(cls):
        cls.conf = dummy_conf()
        utils.conf = cls.conf
        cls.ru = utils.RemoteUser('john', 'dummy_host',
                                  sshkey_path='dummy_key')

    def test_init(self):
        opt = ['-o', 'LogLevel=ERROR', '-o', 'StrictHostKeyChecking=no',
               '-o', 'UserKnownHostsFile=/dev/null']
        ru = utils.RemoteUser('john', 'dummy_host')
        self.assertEqual(opt, ru.opt)
        self.assertEqual('john@dummy_host', ru.host)
        opt = opt + ['-i', 'dummy_key']
        ru = utils.RemoteUser('john', 'dummy_host', sshkey_path='dummy_key')
        self.assertEqual(opt, ru.opt)

    def test_exe(self):
        with patch('managesf.controllers.utils.Popen') as Popen_mock:
            p = Popen_mock.return_value
            self.ru._exe('pwd')
            Popen_mock.assert_called_once_with('pwd', stdout=-1)
            p.wait.assert_any_call()
            p.communicate.assert_any_call()

    def test_ssh(self):
        with patch('managesf.controllers.utils.RemoteUser._exe') as exe_mock:
            cmd = ['ssh'] + self.ru.opt + [self.ru.host] + ['pwd']
            self.ru._ssh('pwd')
            exe_mock.assert_called_once_with(cmd)

    def test__scpFromRemote(self):
        with patch('managesf.controllers.utils.RemoteUser._exe') as exe_mock:
            src = 'dummy_host1'
            dest = 'dummy_host2'
            src = '%s:%s' % (self.ru.host, src)
            cmd = ['scp'] + self.ru.opt + [src, dest]
            self.ru._scpFromRemote('dummy_host1', 'dummy_host2')
            exe_mock.assert_called_once_with(cmd)

    def test__scpToRemote(self):
        with patch('managesf.controllers.utils.RemoteUser._exe') as exe_mock:
            src = 'dummy_host1'
            dest = 'dummy_host2'
            dest = '%s:%s' % (self.ru.host, dest)
            cmd = ['scp'] + self.ru.opt + [src, dest]
            self.ru._scpToRemote('dummy_host1', 'dummy_host2')
            exe_mock.assert_called_once_with(cmd)
