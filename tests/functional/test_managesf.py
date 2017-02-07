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

import requests

from utils import Base
from utils import ManageSfUtils
from utils import ResourcesUtils
from utils import skipIfServiceMissing, skipIfServicePresent

from pysflib.sfgerrit import GerritUtils


class TestConditionalTesting(Base):
    """Functional tests validating the service decorators. If the tests
    are not skipped as expected, fail the tests.
    """
    @skipIfServiceMissing('SomeLameFantasyServiceThatDoesNotExist')
    def test_skip_if_service_missing(self):
        self.fail('Failure to detect that a service is missing')

    # assuming gerrit will always be there ...
    @skipIfServicePresent('gerrit')
    def test_skip_if_service_present(self):
        self.fail('Failure to detect that a service is present')


class TestManageSF(Base):
    """ Functional tests that validate managesf features.
    """
    def setUp(self):
        super(TestManageSF, self).setUp()
        self.projects = []
        self.dirs_to_delete = []
        self.ru = ResourcesUtils()
        self.msu = ManageSfUtils(config.GATEWAY_URL)
        self.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])

    def tearDown(self):
        super(TestManageSF, self).tearDown()
        for name in self.projects:
            self.ru.direct_delete_repo(name)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def create_project(self, name):
        self.ru.direct_create_repo(name)
        self.projects.append(name)

    def test_api_key_auth_with_sfmanager(self):
        """Test the api key auth workflow"""
        user2_cookies = dict(
            auth_pubtkt=config.USERS[config.USER_2]['auth_cookie'])
        url = "https://%s%s" % (config.GATEWAY_HOST, "/auth/apikey/")
        create_key = requests.post(url, cookies=user2_cookies)
        self.assertIn(create_key.status_code, (201, 409))
        key = requests.get(url, cookies=user2_cookies).json().get('api_key')
        # call a simple command that needs authentication
        cmd = "sfmanager --url %s --auth-server-url " \
            "%s --api-key %s sf_user list" % (config.GATEWAY_URL,
                                              config.GATEWAY_URL,
                                              key)
        users = self.msu.exe(cmd)
        self.assertTrue(config.USER_2 in users,
                        "'%s' returned %s" % (cmd, users))
