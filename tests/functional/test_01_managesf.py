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

import os
import config

from utils import Base
from utils import ManageRestServer
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import create_random_str
from utils import GerritUtil
#from utils import RedmineUtil


class TestManageSF(Base):
    """ Functional tests that validate managesf feature.
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

    def test_01_create_public_project_as_admin(self):
        """ Verify the correct creation of a public project
        on both redmine and gerrit
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        #rm = RedmineUtil(config.REDMINE_SERVER, username=config.ADMIN_USER,
        #                 password=config.ADMIN_PASSWD)
        assert gu.isPrjExist(pname)
        assert gu.isGroupExist('%s-core' % pname)
        assert gu.isGroupExist('%s-ptl' % pname)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-core' % pname)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        #assert rm.isProjectExist(pname)

    def test_02_delete_public_project_as_admin(self):
        """ Verify the correct deletion of a public project
        on both redmine and gerrit.
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        #rm = RedmineUtil(config.REDMINE_SERVER, username=config.ADMIN_USER,
        #                 password=config.ADMIN_PASSWD)
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        assert gu.isPrjExist(pname)
        #assert rm.isProjectExist(pname)
        self.msu.deleteProject(pname, config.ADMIN_USER, config.ADMIN_PASSWD)
        assert not gu.isPrjExist(pname)
        assert not gu.isGroupExist('%s-core' % pname)
        assert not gu.isGroupExist('%s-ptl' % pname)
        #assert not rm.isProjectExist(pname)
        self.projects.remove(pname)

    def test_03_create_public_project_as_user_clone_as_admin(self):
        """ Verify we can clone a public project as Admin user
        and .gitreview exist in the master branch
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.ADMIN_EMAIL)
        url = "ssh://%s@%s/%s" % (config.ADMIN_USER,
                                  config.GERRIT_HOST, pname)
        clone_dir = ggu.clone(url, pname)
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))
        # Verify meta/config branch own both group and ACLs config file
        ggu.fetch_meta_config(clone_dir)
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'project.config')))
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'groups')))
