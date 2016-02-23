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
import requests
import time
import urllib2

from utils import Base
from utils import ManageSfUtils
from utils import skip
from utils import skipIfServiceMissing, is_present

from pysflib.sfredmine import RedmineUtils
from pysflib.sfgerrit import GerritUtils
from pysflib.sfauth import get_cookie


class TestUserdata(Base):
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_URL)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.rm = RedmineUtils(
            config.GATEWAY_URL + "/redmine/",
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.gu = GerritUtils(
            config.GATEWAY_URL,
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

    def logout(self):
        url = config.GATEWAY_URL + '/auth/logout/'
        requests.get(url)

    def login(self, username, password, redirect='/'):
        url = config.GATEWAY_URL + "/auth/login"
        data = {'username': username,
                'password': password,
                'back': redirect}
        return requests.post(url, data=data)

    def test_login_redirect_to_jenkins(self):
        """ Verify the user creation and the login
        """
        self.logout()
        url = config.GATEWAY_URL + "jenkins/"
        quoted_url = urllib2.quote(url, safe='')
        response = self.login('user5', config.ADMIN_PASSWORD, quoted_url)

        self.assertEqual(url, response.url)
        # verify if user is created in gerrit and redmine
        self.verify_userdata_gerrit('user5')
        if is_present("SFRedmine"):
            self.verify_userdata_redmine('user5')

    @skipIfServiceMissing('SFRedmine')
    def test_login_redirect_to_redmine(self):
        """ Verify the redirect to redmine project page
        """
        self.logout()
        url = config.GATEWAY_URL + "redmine/projects"
        quoted_url = urllib2.quote(url, safe='')
        response = self.login('user5', config.ADMIN_PASSWORD, quoted_url)

        self.assertEqual(url, response.url)
        # verify if user is created in gerrit and redmine
        self.verify_userdata_gerrit('user5')
        self.verify_userdata_redmine('user5')

    def test_invalid_user_login(self):
        """ Try to login with an invalid user
        """
        self.logout()
        response = self.login('toto', 'nopass', '/')
        self.assertEqual(response.status_code, 401)

    def test_hook_user_login(self):
        """ Functional test when trying to login with service user
        """
        self.logout()
        response = self.login(config.HOOK_USER,
                              config.HOOK_USER_PASSWORD,
                              '/')
        self.assertTrue(response.status_code < 400)

    def test_create_local_user_and_login(self):
        """ Try to create a local user then login
        """
        try:
            self.msu.create_user('Flea', 'RHCP', 'flea@slapdabass.com')
        except NotImplementedError:
            skip("user management not supported in this version of managesf")
        self.logout()
        url = config.GATEWAY_URL + "/dashboard/"
        quoted_url = urllib2.quote(url, safe='')
        response = self.login('Flea', 'RHCP', quoted_url)
        self.assertEqual(url, response.url)

    @skipIfServiceMissing('SFRedmine')
    def test_nonmember_backlog_permissions(self):
        """Make sure project non members can see the backlog and add
        stories"""
        # default value, skip gracefully if it cannot be found
        try:
            non_member_role = self.rm.r.role.get(1)
            assert non_member_role.name == 'Non member'
        except:
            self.skipTest("Could not fetch non-member permissions")
        self.assertTrue('view_master_backlog' in non_member_role.permissions)
        self.assertTrue('create_stories' in non_member_role.permissions)

    def test_delete_user_in_backends_by_username(self):
        """ Delete a user previously registered user by username
        """
        # first, create a user and register it with services
        try:
            self.msu.create_user('bootsy', 'collins', 'funk@mothership.com')
        except NotImplementedError:
            skip("user management not supported in this version of managesf")
        self.logout()
        self.login('bootsy', 'collins', config.GATEWAY_URL)
        # make sure user is in redmine and gerrit
        self.assertEqual('funk@mothership.com',
                         self.gu.get_account('bootsy').get('email'))
        if is_present("SFRedmine"):
            users = self.rm.r.user.filter(limit=20)
            users = [u for u in users if u.firstname == 'bootsy']
            self.assertEqual(1, len(users))
            user = users[0]
            self.assertEqual('funk@mothership.com',
                             user.mail)
        # now suppress it
        del_url = config.GATEWAY_URL + 'manage/services_users/?username=bootsy'
        # try with a a non-admin user, it should not work ...
        auth_cookie = get_cookie(config.GATEWAY_HOST,
                                 'user5', config.ADMIN_PASSWORD)
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertEqual(401,
                         int(d.status_code))
        # try with an admin ...
        auth_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(int(d.status_code) < 400, d.status_code)
        # make sure the user does not exist anymore
        self.assertEqual(False,
                         self.gu.get_account('bootsy'))
        if is_present("SFRedmine"):
            users = self.rm.r.user.filter(limit=20)
            self.assertEqual(0,
                             len([u for u in users
                                  if u.firstname == 'bootsy']))

    def test_delete_user_in_backends_by_email(self):
        """ Delete a user previously registered user by email
        """
        # first, create a user and register it with services
        try:
            self.msu.create_user('josh', 'homme', 'queen@stoneage.com')
        except NotImplementedError:
            skip("user management not supported in this version of managesf")
        self.logout()
        self.login('josh', 'homme', config.GATEWAY_URL)
        # make sure user is in redmine and gerrit
        self.assertEqual('queen@stoneage.com',
                         self.gu.get_account('josh').get('email'))
        if is_present("SFRedmine"):
            users = self.rm.r.user.filter(limit=20)
            users = [u for u in users if u.firstname == 'josh']
            self.assertEqual(1, len(users))
            user = users[0]
            self.assertEqual('queen@stoneage.com',
                             user.mail)
        # now suppress it
        del_url = config.GATEWAY_URL +\
            'manage/services_users/?email=queen@stoneage.com'
        auth_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(int(d.status_code) < 400, d.status_code)
        # make sure the user does not exist anymore
        self.assertEqual(False,
                         self.gu.get_account('josh'))
        if is_present("SFRedmine"):
            users = self.rm.r.user.filter(limit=20)
            self.assertEqual(0,
                             len([u for u in users if u.firstname == 'josh']))

    def test_delete_in_backend_and_recreate(self):
        """Make sure we can recreate a user but as a different one"""
        # first, create a user and register it with services
        try:
            self.msu.create_user('freddie', 'mercury', 'mrbadguy@queen.com')
        except NotImplementedError:
            skip("user management not supported in this version of managesf")
        self.logout()
        self.login('freddie', 'mercury', config.GATEWAY_URL)
        gerrit_id = self.gu.get_account('freddie').get('_account_id')
        if is_present("SFRedmine"):
            users = self.rm.r.user.filter(limit=20)
            user = [u for u in users if u.firstname == 'freddie'][0]
            redmine_id = user.id
        del_url = config.GATEWAY_URL +\
            'manage/services_users/?email=mrbadguy@queen.com'
        auth_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(int(d.status_code) < 400, d.status_code)
        self.assertEqual(False,
                         self.gu.get_account('freddie'))
        if is_present("SFRedmine"):
            users = self.rm.r.user.filter(limit=20)
            self.assertEqual(0,
                             len([u for u in users
                                  if u.firstname == 'freddie']))
        # recreate the user in the backends
        time.sleep(5)
        self.logout()
        self.login('freddie', 'mercury', config.GATEWAY_URL)
        new_gerrit_id = self.gu.get_account('freddie').get('_account_id')
        self.assertTrue(gerrit_id != new_gerrit_id)
        if is_present("SFRedmine"):
            users = self.rm.r.user.filter(limit=20)
            user = [u for u in users if u.firstname == 'freddie'][0]
            new_redmine_id = user.id
            self.assertTrue(redmine_id != new_redmine_id)
