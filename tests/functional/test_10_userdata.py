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
import json
import os
import requests
import shutil
import yaml

from utils import Base


class TestUserdata(Base):
    @classmethod
    def setUpClass(cls):
        with open(os.environ['SF_ROOT'] + "/build/hiera/redmine.yaml") as f:
            ry = yaml.load(f)
        cls.redmine_api_key = ry['redmine']['issues_tracker_api_key']
        cls.user5_email = 'user5@%s' % os.environ['SF_SUFFIX']
        data = {'username': 'user5', 'password': 'userpass', 'back': '/'}
        # Trigger a login as user5, this should fetch the userdata from LDAP
        url = "http://%s/auth/login/" % config.GATEWAY_HOST
        resp=requests.post(url, data=data)

    def test_ldap_userdata_gerrit(self):
        # Now check that the correct data was stored in Gerrit
        url = "http://gerrit.%s/api/accounts/user5" % os.environ['SF_SUFFIX']
        resp=requests.get(url)
        data = json.loads(resp.content[4:])
        self.assertEqual('Demo user5', data.get('name'))
        self.assertEqual(self.user5_email, data.get('email'))

    def test_ldap_userdata_redmine(self):
        headers = {'X-Redmine-API-Key': self.redmine_api_key,
                   'Content-Type': 'application/json'}
        user5 = {}
        # We need to iterate over the existing users
        for i in range(10):  # check only the first 10 user ids
            url = 'http://api-redmine.%s/users/%d.json' % (os.environ['SF_SUFFIX'], i)
            resp=requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                user = data.get('user')
                if user.get('login') == 'user5':
                    user5 = user
        self.assertEqual('Demo user5', user5.get('lastname'))
        self.assertEqual(self.user5_email, user5.get('mail'))
