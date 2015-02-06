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

from sfmigration.issues import github
from sfmigration.tests.issues import common


test_version = {'number': 1,
                'title': '0.1.0',
                'state': 'closed'}


test_issue = {'id': 1,
              'title': 'test feature',
              'body': 'the best feature in the universe',
              'state': 'open',
              'milestone': test_version,
              'assignee': {'id': '3',
                           'login': 'kenny'}}


class TestGithubImporter(common.BaseTestImporter):

    @classmethod
    def setupClass(cls):
        cls.importer = github.GithubImporter(repository='nova',
                                             repo_owner='openstack')
        cls.expected_issue = {
            'source_id': test_issue['id'],
            'priority_id': 1,
            'subject': test_issue['title'],
            'description': test_issue['body'],
            'status_name': test_issue['state'].title(),
            'fixed_version_id': test_issue['milestone']['number'],
            'version_name': test_issue['milestone']['title'],
            'assigned_to_id': test_issue['assignee']['id'],
            'assigned_to_login': test_issue['assignee']['login'], }
        cls.expected_version = {
            'source_id': test_version['number'],
            'name': test_version['title'],
            'status': test_version['state'], }
        cls.test_version = test_version
        cls.test_issue = test_issue
        cls.fetch_versions_call_to_patch = ('github3.repos'
                                            '.Repository.milestones')
        cls.fetch_issues_call_to_patch = ('github3.repos'
                                          '.Repository.issues')
