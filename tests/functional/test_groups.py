# Copyright (C) 2016 Red Hat
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

from utils import Base
from utils import ManageSfUtils
from utils import create_random_str
from utils import has_issue_tracker
from utils import get_issue_tracker_utils

from pysflib.sfgerrit import GerritUtils


class Testgroups(Base):
    """ Functional tests that validate standalone groups.
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_URL)
        cls.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        cls.rm = get_issue_tracker_utils(
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])

    def test_standalone_group(self):
        """ Test a standalone group can be managed
        """
        groupname = "grp/%s" % create_random_str()

        # Create the group
        self.msu.create_or_delete_group("admin",
                                        groupname)
        # Test group exist on Gerrit
        self.assertIn(groupname, self.gu.get_groups().keys())
        # Test group exists on the issue tracker
        if has_issue_tracker():
            self.assertTrue(self.rm.get_group_id(groupname))

        # Add members in the group
        self.msu.add_or_remove_to_group("admin", groupname,
                                        ["user2@sftests.com",
                                         "user3@sftests.com"])

        # Check members on Gerrit
        gid = self.gu.get_group_id(groupname)
        members = [m['email'] for m in self.gu.get_group_members(gid)]
        self.assertIn("user2@sftests.com", members)
        self.assertIn("user3@sftests.com", members)
        # Check members on the issue tracker
        if has_issue_tracker():
            gid = self.rm.get_group_id(groupname)
            self.assertTrue(len(self.rm.list_group(gid)), 3)

        # Remve members from the group
        self.msu.add_or_remove_to_group("admin", groupname,
                                        ["user2@sftests.com",
                                         "user3@sftests.com"],
                                        "remove")
        # Check members on Gerrit
        gid = self.gu.get_group_id(groupname)
        members = [m['email'] for m in self.gu.get_group_members(gid)]
        self.assertNotIn("user2@sftests.com", members)
        self.assertNotIn("user3@sftests.com", members)
        # Check members on the issue tracker
        if has_issue_tracker():
            gid = self.rm.get_group_id(groupname)
            self.assertTrue(len(self.rm.list_group(gid)), 1)

        # Delete the group
        self.msu.create_or_delete_group("admin",
                                        groupname, "delete")
        # Test group does not exist on Gerrit
        self.assertNotIn(groupname, self.gu.get_groups().keys())
        # Test group does not exists on the issue tracker
        if has_issue_tracker():
            self.assertFalse(self.rm.get_group_id(groupname))
