#!/bin/env python
# -*- coding: utf-8 -*-
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
import json
import requests
import time
import urllib2
import warnings

from utils import Base
from utils import ManageSfUtils
from utils import skip
from utils import skipIfIssueTrackerMissing, has_issue_tracker
from utils import get_issue_tracker_utils
from utils import get_cookie

from pysflib.sfgerrit import GerritUtils


class TestUserdata(Base):
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_URL)
        cls.rm = get_issue_tracker_utils(
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        cls.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])

    def verify_userdata_gerrit(self, login):
        # Now check that the correct data was stored in Gerrit
        data = self.gu.get_account(login)
        self.assertEqual(config.USERS[login]['lastname'], data.get('name'))
        self.assertEqual(config.USERS[login]['email'], data.get('email'))

    def verify_userdata_issue_tracker(self, login):
        users = self.rm.active_users()
        user = [u for u in users if u[0] == login][0]
        self.assertEqual(login + " " + config.USERS[login]['lastname'],
                         user[2])
        self.assertEqual(config.USERS[login]['email'], user[1])

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
        url = config.GATEWAY_URL + "/jenkins/"
        quoted_url = urllib2.quote(url, safe='')
        response = self.login('user5', config.ADMIN_PASSWORD, quoted_url)

        self.assertEqual(url, response.url)
        # verify if user is created in gerrit and tracker
        self.verify_userdata_gerrit('user5')
        if has_issue_tracker():
            self.verify_userdata_issue_tracker('user5')

    @skipIfIssueTrackerMissing()
    def test_login_redirect_to_issue_tracker(self):
        """ Verify the redirect to tracker project page
        """
        self.logout()
        url = self.rm.get_sf_projects_url()
        quoted_url = urllib2.quote(url, safe='')
        response = self.login('user5', config.ADMIN_PASSWORD, quoted_url)

        self.assertEqual(url, response.url)
        # verify if user is created in gerrit and issue tracker
        self.verify_userdata_gerrit('user5')
        self.verify_userdata_issue_tracker('user5')

    def test_invalid_user_login(self):
        """ Try to login with an invalid user
        """
        self.logout()
        response = self.login('toto', 'nopass', '/')
        self.assertEqual(response.status_code, 401)

    @skipIfIssueTrackerMissing()
    def test_hook_user_login(self):
        """ Functional test when trying to reach redmine with service user
        """
        self.logout()
        response = self.login(config.HOOK_USER,
                              config.HOOK_USER_PASSWORD,
                              '/redmine/')
        self.assertTrue(response.status_code < 400)

    def test_create_local_user_and_login(self):
        """ Try to create a local user then login
        """
        try:
            self.msu.create_user('Flea', 'RHCP', 'flea@slapdabass.com')
        except NotImplementedError:
            skip("user management not supported in this version of managesf")
        self.logout()
        url = config.GATEWAY_URL + "/sf/welcome.html"
        quoted_url = urllib2.quote(url, safe='')
        response = self.login('Flea', 'RHCP', quoted_url)
        self.assertEqual(url, response.url)

    @skipIfIssueTrackerMissing()
    def test_nonmember_backlog_permissions(self):
        """Make sure project non members can see the backlog and add
        stories"""
        # default value, skip gracefully if it cannot be found
        try:
            non_member_role = self.rm.get_role(1)
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
        if has_issue_tracker():
            users = self.rm.active_users()
            users = [u for u in users if u[0] == 'bootsy']
            self.assertEqual(1, len(users))
            user = users[0]
            self.assertEqual('funk@mothership.com',
                             user[1])
        # now suppress it
        del_url = config.GATEWAY_URL +\
            '/manage/services_users/?username=bootsy'
        # try with a a non-admin user, it should not work ...
        auth_cookie = get_cookie('user5', config.ADMIN_PASSWORD)
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(400 < int(d.status_code) < 500)
        # try with an admin ...
        auth_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(int(d.status_code) < 400, d.status_code)
        # make sure the user does not exist anymore
        self.assertEqual(False,
                         self.gu.get_account('bootsy'))
        if has_issue_tracker():
            users = self.rm.active_users()
            self.assertEqual(0,
                             len([u for u in users
                                  if u[0] == 'bootsy']))

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
        if has_issue_tracker():
            users = self.rm.active_users()
            users = [u for u in users if u[0] == 'josh']
            self.assertEqual(1, len(users))
            user = users[0]
            self.assertEqual('queen@stoneage.com',
                             user[1])
        # now suppress it
        del_url = config.GATEWAY_URL +\
            '/manage/services_users/?email=queen@stoneage.com'
        auth_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(int(d.status_code) < 400, d.status_code)
        # make sure the user does not exist anymore
        self.assertEqual(False,
                         self.gu.get_account('josh'))
        if has_issue_tracker():
            users = self.rm.active_users()
            self.assertEqual(0,
                             len([u for u in users if u[0] == 'josh']))

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
        if has_issue_tracker():
            tracker_id = self.rm.get_user_id_by_username('freddie')
        del_url = config.GATEWAY_URL +\
            '/manage/services_users/?email=mrbadguy@queen.com'
        auth_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(int(d.status_code) < 400, d.status_code)
        self.assertEqual(False,
                         self.gu.get_account('freddie'))
        if has_issue_tracker():
            users = self.rm.active_users()
            self.assertEqual(0,
                             len([u for u in users
                                  if u[0] == 'freddie']))
        # recreate the user in the backends
        time.sleep(5)
        self.logout()
        self.login('freddie', 'mercury', config.GATEWAY_URL)
        new_gerrit_id = self.gu.get_account('freddie').get('_account_id')
        self.assertTrue(gerrit_id != new_gerrit_id)
        if has_issue_tracker():
            new_tracker_id = self.rm.get_user_id_by_username('freddie')
            self.assertTrue(tracker_id != new_tracker_id)

    def test_unicode_user(self):
        """ Try to create a local user with unicode charset, login, delete
        """
        # /!\ redmine does not support non-ASCII chars in usernames.
        auth_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']
        try:
            self.msu.create_user('naruto', 'rasengan', 'datte@bayo.org',
                                 fullname=u'うずまきナルト')
        except NotImplementedError:
            skip("user management not supported in this version of managesf")
        except UnicodeEncodeError:
            # TODO the CLI works but I can't find what is wrong with
            # python's handling of unicode in subprocess.
            warnings.warn('Cannot run shell command with unicode chars for '
                          'whatever reason, retrying with a direct REST '
                          'API call ...',
                          UnicodeWarning)
            create_url = config.GATEWAY_URL + "/manage/user/naruto"
            headers = {'Content-Type': 'application/json; charset=utf8'}
            data = {'email': 'datte@bayo.org',
                    'fullname': u'うずまきナルト'.encode('utf8'),
                    'password': 'rasengan'}
            create_user = requests.post(create_url,
                                        headers=headers,
                                        data=json.dumps(data),
                                        cookies={'auth_pubtkt': auth_cookie})
            self.assertEqual(201,
                             int(create_user.status_code))
        self.logout()
        url = config.GATEWAY_URL + "/sf/welcome.html"
        quoted_url = urllib2.quote(url, safe='')
        response = self.login('naruto',
                              'rasengan', quoted_url)
        self.assertEqual(url, response.url)
        naru_gerrit = self.gu.get_account('naruto')
        self.assertEqual(u'うずまきナルト',
                         naru_gerrit.get('name'))
        # TODO this should be tested in the tracker as well
        del_url = config.GATEWAY_URL +\
            '/manage/services_users/?email=datte@bayo.org'
        d = requests.delete(del_url,
                            cookies={'auth_pubtkt': auth_cookie})
        self.assertTrue(int(d.status_code) < 400, d.status_code)
        self.assertEqual(False,
                         self.gu.get_account('naruto'))
