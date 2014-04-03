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

import unittest
from mock import patch
import export_issues
import redmine


class TestIssueImporter(unittest.TestCase):

    def setup(self):
        pass

    def test_get_config_value(self):
        pid = export_issues.get_config_value('REDMINE', 'name')
        self.assertIsNotNone(pid)

    def test_get_config_value_wrong_option(self):
        pid = export_issues.get_config_value('REDMINE', 'abc')
        self.assertIsNone(pid)

    def test_get_config_value_wrong_section(self):
        pid = export_issues.get_config_value('xyz', 'id')
        self.assertIsNone(pid)

    @patch.object(redmine.managers.ResourceManager, 'create')
    def test_main(self, mock_create):
        assert redmine.managers.ResourceManager.create is mock_create
        mock_create.return_value = None
        try:
            export_issues.main()
        except:
            self.fail("Exception thrown")


if __name__ == '__main__':
    unittest.main()
