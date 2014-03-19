#!/usr/bin/python

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
