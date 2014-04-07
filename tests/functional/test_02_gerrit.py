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

import config

from utils import Base
from utils import ManageRestServer
from utils import ManageSfUtils
#from utils import GerritGitUtils
from utils import create_random_str
from utils import GerritUtil
#from utils import RedmineUtil


class TestGerrit(Base):
    """ Functional tests that validate some gerrit behaviors.
    """
    @classmethod
    def setUpClass(cls):
        cls.projects = []
        cls.clone_dirs = []
        cls.mrs = ManageRestServer()
        cls.mrs.run()
        cls.msu = ManageSfUtils('localhost', 9090)

    @classmethod
    def tearDownClass(cls):
        for name in cls.projects:
            cls.msu.deleteProject(name,
                                  config.ADMIN_USER,
                                  config.ADMIN_PASSWD)
        cls.mrs.stop()

    def createProject(self, name):
        self.msu.createProject(name,
                               config.ADMIN_USER,
                               config.ADMIN_PASSWD)
        self.projects.append(name)

    def test_01_add_remove_user_in_core_as_admin(self):
        """ Verify we can add/remove user from core group
        as admin
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        assert gu.isPrjExist(pname)
        NEW_USER = 'christian.schwede'
        GROUP_NAME = '%s-core' % pname
        assert gu.isGroupExist(GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.addGroupMember(NEW_USER, GROUP_NAME)
        assert gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.deleteGroupMember(NEW_USER, GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)

    def test_add_remove_user_in_ptl_as_admin(self):
        """ Verify we can add/remove user from ptl group
        as admin
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        assert gu.isPrjExist(pname)
        NEW_USER = 'christian.schwede'
        GROUP_NAME = '%s-ptl' % pname
        assert gu.isGroupExist(GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.addGroupMember(NEW_USER, GROUP_NAME)
        assert gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.deleteGroupMember(NEW_USER, GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)
