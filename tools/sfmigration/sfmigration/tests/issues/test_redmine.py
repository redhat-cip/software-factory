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

import json
from collections import namedtuple
from unittest import TestCase

import mock

from sfmigration.issues import redmine


def json_to_object(j):
    j_ = json.dumps(j)
    hook = lambda d: namedtuple('Whatevs', d.keys())(*d.values())
    return json.loads(j_,
                      object_hook=hook)


test_version = {'id': 1,
                'name': '0.1.0',
                'status': 'closed'}


test_issue = {'id': 1,
              'subject': 'test feature',
              'description': 'the best feature in the universe',
              'tracker': {'id': 2,
                          'name': 'User story'},
              'status': {'id': 3,
                         'name': 'In Progress'},
              'priority': {'id': 4,
                           'name': 'Urgent'},
              'done_ratio': 50,
              'story_points': 13,
              'fixed_version': test_version, }


class TestRedmineImporter(TestCase):

    @classmethod
    def setupClass(cls):
        cls.redmine = redmine.RedmineImporter(username='wendy',
                                              password='testaburger',
                                              id=1,
                                              url='http://fake/redmine',
                                              name='glitter and sparkles')

    def test_fetch_versions(self):
        filter_response = iter([json_to_object(test_version), ])
        with mock.patch('redmine.managers.ResourceManager.filter',
                        return_value=filter_response):
            results = [v for v in self.redmine.fetch_versions()]
            self.assertEqual(1, len(results))
            result = results[0]
            expected = {'source_id': test_version['id'],
                        'name': test_version['name'],
                        'status': test_version['status']}
            self.assertEqual(expected, result)

    def test_fetch_issues(self):
        filter_response = iter([json_to_object(test_issue), ])
        with mock.patch('redmine.managers.ResourceManager.filter',
                        return_value=filter_response):
            results = [v for v in self.redmine.fetch_issues()]
            self.assertEqual(1, len(results))
            result = results[0]
            expected = {'source_id': test_issue['id'],
                        'priority_id': test_issue['priority']['id'],
                        'subject': test_issue['subject'],
                        'description': test_issue['description'],
                        'tracker_id': test_issue['tracker']['id'],
                        'tracker_name': test_issue['tracker']['name'],
                        'status_id': test_issue['status']['id'],
                        'status_name': test_issue['status']['name'],
                        'priority_id': test_issue['priority']['id'],
                        'priority_name': test_issue['priority']['name'],
                        'done_ratio': test_issue['done_ratio'],
                        'story_points': test_issue['story_points'],
                        'fixed_version_id': test_issue['fixed_version']['id'],
                        'version_name': test_issue['fixed_version']['name'], }
            self.assertEqual(expected, result)
