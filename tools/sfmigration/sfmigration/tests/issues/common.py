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

from sfmigration.common import base


def json_to_object(j):
    j_ = json.dumps(j)
    hook = lambda d: namedtuple('Whatevs', d.keys())(*d.values())  # flake8: noqa
    return json.loads(j_,
                      object_hook=hook)


class BaseTestImporter(TestCase):

    @classmethod
    def setupClass(cls):
        cls.importer = base.BaseIssueImporter()
        cls.expected_issue = {}
        cls.expected_version = {}
        cls.test_version = {}
        cls.test_issue = {}
        cls.fetch_versions_call_to_patch = ''
        cls.fetch_issues_call_to_patch = ''

    def _test_result(self, call_to_test):
        if call_to_test == 'versions':
            method = self.importer.fetch_versions
            expected = self.expected_version
        elif call_to_test == 'issues':
            method = self.importer.fetch_issues
            expected = self.expected_issue
        else:
            raise ValueError('Unknown call to test')
        results = [v for v in method()]
        self.assertEqual(1, len(results))
        result = results[0]
        self.assertEqual(expected, result)

    def test_fetch_versions(self):
        filter_response = iter([json_to_object(self.test_version), ])
        with mock.patch(self.fetch_versions_call_to_patch,
                        return_value=filter_response):
            self._test_result('versions')

    def test_fetch_issues(self):
        filter_response = iter([json_to_object(self.test_issue), ])
        with mock.patch(self.fetch_issues_call_to_patch,
                        return_value=filter_response):
            self._test_result('issues')
