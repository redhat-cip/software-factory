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
import requests
import urllib

from utils import Base
from utils import ManageSfUtils

from pysflib.sfredmine import RedmineUtils
from pysflib.sfgerrit import GerritUtils


class TestUserdata(Base):
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_HOST, 80)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.rm = RedmineUtils(
            'http://%s' % config.REDMINE_HOST,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.gu = GerritUtils(
            'http://%s' % config.GERRIT_HOST,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)

    def create_project(self, name, user, options=None,
                       cookie=None):
        self.msu.createProject(name, user, options,
                               cookie)
        self.projects.append(name)

    def verify_userdata_gerrit(self, login):
        # Now check that the correct data was stored in Gerrit
        data = self.gu.get_account(login)
        self.assertEqual(config.USERS[login]['lastname'], data.get('name'))
        self.assertEqual(config.USERS[login]['email'], data.get('email'))

    def verify_userdata_redmine(self, login):
        users = self.rm.r.user.filter(limit=10)
        user = [u for u in users if u.firstname == login][0]
        self.assertEqual(config.USERS[login]['lastname'], user.lastname)
        self.assertEqual(config.USERS[login]['email'], user.mail)

    def test_userdata_ldap(self):
        """ Functional tests to verify the ldap user
        """
        data = {'username': 'user5', 'password': 'userpass', 'back': '/'}
        # Trigger a login as user5, this should fetch the userdata from LDAP
        url = "http://%s/auth/login/" % config.GATEWAY_HOST
        requests.post(url, data=data, allow_redirects=False)

        # verify if ldap user is created in gerrit and redmine
        self.verify_userdata_gerrit('user5')
        self.verify_userdata_redmine('user5')

    def test_userdata_github(self):
        """ Functional tests to verify the github user
        """
        # Trigger a oauth login as user6,
        # this should fetch the userdata from oauth mock
        # allow_redirects=False is not working for GET
        github_url = "http://%s/auth/login/github" % config.GATEWAY_HOST
        url = github_url + "?" + \
            urllib.urlencode({'username': 'user6',
                              'password': 'userpass',
                              'back': '/'})
        resp = requests.get(url)
        for r in resp.history:
            if r.cookies:
                for cookie in r.cookies:
                    if 'auth_pubtkt' == cookie.name:
                        config.USERS['user6']['auth_cookie'] = cookie.value
                        break
            if config.USERS['user6']['auth_cookie'] != "":
                break

        # verify if github user is created in gerrit and redmine
        self.verify_userdata_gerrit('user6')
        self.verify_userdata_redmine('user6')
