#!/usr/bin/env python
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


from mock import patch
from unittest import TestCase
# initialize the log capture before loading the module's logger
from testfixtures import LogCapture
l = LogCapture()  # flake8: noqa

from redmine.managers import ResourceBadMethodError

from sfmigration.common import base
from sfmigration.common import softwarefactory as sf


test_issue = {'source_id': 1,
              'priority_id': 2,
              'subject': 'test subject',
              'description': 'test description',
              'tracker_id': 3,
              # 'tracker_name': 'test tracker',
              'status_id': 4,
              # 'status_name': 'test status',
              'priority_id': 5,
              # 'priority_name': 'test priority',
              'done_ratio': 100,
              'story_points': 13,
              'fixed_version_id': 6,
              # 'version_name': 'test version',
              # 'assigned_to_login': 'Leopold Butters Stotch',
              'assigned_to_id': 7}


class MockIssue:
    def __getattr__(self, x):
        return test_issue[x]


class _TestIssueImporter(base.BaseIssueImporter):
    def fetch_issues(self):
        yield test_issue

    def fetch_trackers(self):
        raise NotImplementedError

    def fetch_wiki(self):
        raise NotImplementedError

    def fetch_issue_statuses(self):
        yield {'name': 'test status'}

    def fetch_users(self):
        raise NotImplementedError

    def fetch_versions(self):
        raise NotImplementedError


def get_cookie_(*args, **kwargs):
    return '1234'


def raise_(*args, **kwargs):
    raise ResourceBadMethodError


class TestMigrationToSFRedmine(TestCase):
    @classmethod
    def setupClass(cls):
        with patch('pysflib.sfauth.get_cookie',
                   new_callable=lambda: get_cookie_):
            cls.sfredmine = sf.SFRedmineMigrator(username='mackey',
                                                 password='mmmkay',
                                                 id=1,
                                                 url='https://fake/redmine',
                                                 name='test project',
                                                 sf_domain='fake',
                                                 versions_to_skip=None,
                                                 issues_to_skip=None)
        cls.importer = _TestIssueImporter()

    def test_api_method_validation(self):
        self.sfredmine.migrate_versions(self.importer)
        with patch('redmine.managers.ResourceManager.create',
                   new_callable=lambda: raise_):
            self.sfredmine.migrate_issue_statuses(self.importer)
            l.check(('root', 'WARNING',
                     'Importing versions is not supported, skipping.'),
                    ('root', 'WARNING',
                     ('Creating issue statuses not supported '
                      'by redmine API, skipping.')),)

    def test_migrate_issues(self):
        with patch('redmine.managers.ResourceManager.create') as m:
            m.return_value = MockIssue()
            self.sfredmine.migrate_issues(self.importer)
            self.assertEqual(1, m.call_count)

    @classmethod
    def teardownClass(cls):
        l.uninstall()
