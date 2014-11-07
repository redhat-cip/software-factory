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
from contextlib import nested
from pecan.core import exc

from managesf.controllers import backup
from managesf.tests import dummy_conf


class TestBackup(TestCase):
    @classmethod
    def setupClass(cls):
        cls.conf = dummy_conf()
        backup.conf = cls.conf

    def test_init(self):
        ctx = [patch('managesf.controllers.backup.user_is_administrator'),
               patch('managesf.controllers.backup.RemoteUser')]
        with nested(*ctx) as (uia, ru):
            uia.return_value = False
            self.assertRaises(exc.HTTPUnauthorized, lambda: backup.Backup())
            uia.return_value = True
            backup.Backup()
            self.assertEqual(3, len(ru.mock_calls))

    def test_start(self):
        ctx = [patch('managesf.controllers.backup.user_is_administrator'),
               patch('managesf.controllers.backup.Backup.check_for_service'),
               patch('managesf.controllers.backup.RemoteUser._ssh')]
        with nested(*ctx) as (uia, cfs, ssh):
            uia.return_value = True
            backup.Backup().start()
            self.assertTrue(ssh.called)

    def test_get(self):
        ctx = [patch('managesf.controllers.backup.user_is_administrator'),
               patch('managesf.controllers.backup.RemoteUser._scpFromRemote')]
        with nested(*ctx) as (uia, scp):
            uia.return_value = True
            backup.Backup().get()
            self.assertTrue(scp.called)

    def test_restore(self):
        ctx = [patch('managesf.controllers.backup.user_is_administrator'),
               patch('managesf.controllers.backup.RemoteUser._ssh'),
               patch('managesf.controllers.backup.Backup.check_for_service'),
               patch('managesf.controllers.backup.RemoteUser._scpToRemote')]

        with nested(*ctx) as (uia, ssh, cfs, scp):
            uia.return_value = True
            backup.Backup().restore()
            self.assertTrue(scp.called)
            self.assertTrue(ssh.called)

    def test_backup_ops(self):
        ctx = [patch('managesf.controllers.backup.user_is_administrator'),
               patch('managesf.controllers.backup.RemoteUser'),
               patch('managesf.controllers.backup.Backup.start'),
               patch('managesf.controllers.backup.Backup.get'),
               patch('managesf.controllers.backup.Backup.restore')]
        with nested(*ctx) as (uia, ru, s, g, r):
            backup.backup_start()
            self.assertTrue(s.called)
            backup.backup_get()
            self.assertTrue(g.called)
            backup.backup_restore()
            self.assertTrue(r.called)
