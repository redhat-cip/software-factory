#!/bin/env python
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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


from redmine import Redmine


class BaseRedmine(object):
    def __init__(self, username=None, password=None,
                 apikey=None, id=None, url=None, name=None):
        super(BaseRedmine, self).__init__()
        self.username = username
        self.password = password
        self.apikey = apikey
        self.id = id
        self.url = url
        self.name = name
        self._create_connector()

    def _create_connector(self):
        if self.apikey:
            self.redmine = Redmine(self.url, key=self.apikey,
                                   requests={'verify': False})
        else:
            self.redmine = Redmine(self.url, username=self.username,
                                   password=self.password,
                                   requests={'verify': False})


class BaseIssueImporter(object):
    def __init__(self):
        super(BaseIssueImporter, self).__init__()

    def fetch_trackers(self):
        raise NotImplementedError

    def fetch_wiki(self):
        raise NotImplementedError

    def fetch_issue_statuses(self):
        raise NotImplementedError

    def fetch_users(self):
        raise NotImplementedError

    def fetch_versions(self):
        raise NotImplementedError

    def fetch_issues(self):
        raise NotImplementedError
