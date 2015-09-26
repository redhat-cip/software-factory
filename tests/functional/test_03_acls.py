#!/bin/env python
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

from utils import Base
from utils import ManageSfUtils


class TestSFACLs(Base):
    """ Functional tests that validate SF project ACLs.
    """
    @classmethod
    def setUpClass(cls):
        cls.projects = []
        cls.clone_dirs = []
        cls.msu = ManageSfUtils(config.GATEWAY_URL)

    @classmethod
    def tearDownClass(cls):
        for name in cls.projects:
            cls.msu.deleteProject(name,
                                  config.ADMIN_USER)

    def createProject(self, name):
        self.msu.createProject(name,
                               config.ADMIN_USER)
        self.projects.append(name)

    def test_01_validate_gerrit_public_project_acls(self):
        """ Verify the correct behavior of ACLs set on
        gerrit public project
        """
        pass
