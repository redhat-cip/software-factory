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

import json
import requests
import logging
import MySQLdb

from pysflib.sfredmine import RedmineUtils

logger = logging.getLogger(__name__)


class Gerrit:
    def __init__(self, conf):
        self.gerrit_url = "%s/api/a/accounts" % conf.gerrit['url']
        self.admin_user = conf.gerrit['admin_user']
        self.admin_password = conf.gerrit['admin_password']

        self.db_host = conf.gerrit['db_host']
        self.db_name = conf.gerrit['db_name']
        self.db_user = conf.gerrit['db_user']
        self.db_password = conf.gerrit['db_password']

    def install_sshkeys(self, username, keys):
        url = "%s/%s/sshkeys" % (self.gerrit_url, username)
        for entry in keys:
            requests.post(url, data=entry.get('key'),
                          auth=(self.admin_user, self.admin_password))

    def add_in_acc_external(self, account_id, username):
        db = MySQLdb.connect(passwd=self.db_password, db=self.db_name,
                             host=self.db_host, user=self.db_user)
        c = db.cursor()
        sql = ("INSERT INTO account_external_ids VALUES"
               "(%d, NULL, NULL, 'gerrit:%s');" %
               (account_id, username))
        try:
            c.execute(sql)  # Will be only successful if entry does not exist
            db.commit()
            return True
        except:
            return False

    def create_gerrit_user(self, username, email, lastname, keys):
        user = {"name": lastname, "email": email}
        data = json.dumps(user)

        headers = {"Content-type": "application/json"}
        url = "%s/%s" % (self.gerrit_url, username)
        requests.put(url, data=data, headers=headers,
                     auth=(self.admin_user, self.admin_password))

        resp = requests.get(url, headers=headers,
                            auth=(self.admin_user, self.admin_password))
        data = resp.content[4:]  # there is some garbage at the beginning
        try:
            account_id = json.loads(data).get('_account_id')
        except:
            account_id = None

        fetch_ssh_keys = False
        if account_id:
            fetch_ssh_keys = self.add_in_acc_external(account_id, username)

        if keys and fetch_ssh_keys:
            self.install_sshkeys(username, keys)


class UserDetailsCreator:
    def __init__(self, conf):
        self.r = RedmineUtils(conf.redmine['apiurl'],
                              key=conf.redmine['apikey'])
        self.g = Gerrit(conf)

    def create_user(self, username, email, lastname, keys):
        try:
            self.r.create_user(username, email, lastname)
        except Exception, e:
            logger.info('When adding user %s: %s' % (username, str(e)))
        self.g.create_gerrit_user(username, email, lastname, keys)
        # Here we don't care of the error
        return True
