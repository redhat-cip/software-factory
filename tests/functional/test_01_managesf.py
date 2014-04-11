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
import shutil

from utils import Base
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import create_random_str
from utils import set_private_key
from utils import GerritUtil
from utils import RedmineUtil


class TestManageSF(Base):
    """ Functional tests that validate managesf features.
    Here we do basic verifications about project creation
    with managesf.
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.MANAGESF_HOST, 80)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER,
                                   config.ADMIN_PASSWD)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def createProject(self, name, user, passwd,
                      private=False, group_infos=None, upstream=None):
        self.msu.createProject(name, user, passwd,
                               private=private,
                               group_infos=group_infos,
                               upstream=upstream)
        self.projects.append(name)

    def test_create_public_project_as_admin(self):
        """ Create public project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER, config.ADMIN_PASSWD)
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        rm = RedmineUtil(config.REDMINE_SERVER, username=config.ADMIN_USER,
                         password=config.ADMIN_PASSWD)
        assert gu.isPrjExist(pname)
        assert rm.isProjectExist(pname)
        assert gu.isGroupExist('%s-ptl' % pname)
        assert gu.isGroupExist('%s-core' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-core' % pname)

    def test_create_private_project_as_admin(self):
        """ Create private project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER,
                           config.ADMIN_PASSWD, private=True)
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        rm = RedmineUtil(config.REDMINE_SERVER, username=config.ADMIN_USER,
                         password=config.ADMIN_PASSWD)
        assert gu.isPrjExist(pname)
        assert rm.isProjectExist(pname)
        assert gu.isGroupExist('%s-ptl' % pname)
        assert gu.isGroupExist('%s-core' % pname)
        assert gu.isGroupExist('%s-dev' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-core' % pname)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-dev' % pname)

    def test_delete_public_project_as_admin(self):
        """ Delete public project on redmine and gerrit as admin
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        rm = RedmineUtil(config.REDMINE_SERVER, username=config.ADMIN_USER,
                         password=config.ADMIN_PASSWD)
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER, config.ADMIN_PASSWD)
        assert gu.isPrjExist(pname)
        assert rm.isProjectExist(pname)
        self.msu.deleteProject(pname, config.ADMIN_USER, config.ADMIN_PASSWD)
        assert not gu.isPrjExist(pname)
        assert not gu.isGroupExist('%s-ptl' % pname)
        assert not rm.isProjectExist(pname)
        assert not gu.isGroupExist('%s-core' % pname)
        self.projects.remove(pname)

    def test_create_public_project_as_user(self):
        """ Create public project on redmine and gerrit as user
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.USER_2, config.USER_2_PASSWD)
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        rm = RedmineUtil(config.REDMINE_SERVER, username=config.ADMIN_USER,
                         password=config.ADMIN_PASSWD)
        assert gu.isPrjExist(pname)
        assert rm.isProjectExist(pname)
        assert gu.isGroupExist('%s-ptl' % pname)
        assert gu.isGroupExist('%s-core' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        assert gu.isMemberInGroup(config.ADMIN_USER, '%s-core' % pname)

    def test_create_private_project_as_user(self):
        """ Create private project on redmine and gerrit as user
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.USER_2, config.USER_2_PASSWD,
                           private=True)
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER,
                        password=config.ADMIN_PASSWD)
        rm = RedmineUtil(config.REDMINE_SERVER, username=config.ADMIN_USER,
                         password=config.ADMIN_PASSWD)
        assert gu.isPrjExist(pname)
        assert rm.isProjectExist(pname)
        assert gu.isGroupExist('%s-ptl' % pname)
        assert gu.isGroupExist('%s-core' % pname)
        assert gu.isGroupExist('%s-dev' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert gu.isMemberInGroup(config.USER_2, '%s-ptl' % pname)
        assert gu.isMemberInGroup(config.USER_2, '%s-core' % pname)
        assert gu.isMemberInGroup(config.USER_2, '%s-dev' % pname)

    def test_create_public_project_as_admin_clone_as_admin(self):
        """ Clone public project as admin and check content
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER, config.ADMIN_PASSWD)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.ADMIN_EMAIL)
        url = "ssh://%s@%s/%s" % (config.ADMIN_USER,
                                  config.GERRIT_HOST, pname)
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
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
        # There is no group dev for a public project
        content = file(os.path.join(clone_dir, 'project.config')).read()
        self.assertFalse('%s-dev' % pname in content)
        content = file(os.path.join(clone_dir, 'groups')).read()
        self.assertFalse('%s-dev' % pname in content)

    def test_create_private_project_as_admin_clone_as_admin(self):
        """ Clone private project as admin and check content
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER,
                           config.ADMIN_PASSWD,
                           private=True)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.ADMIN_EMAIL)
        url = "ssh://%s@%s/%s" % (config.ADMIN_USER,
                                  config.GERRIT_HOST, pname)
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
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
        # There is a group dev for a private project
        content = file(os.path.join(clone_dir, 'project.config')).read()
        self.assertTrue('%s-dev' % pname in content)
        content = file(os.path.join(clone_dir, 'groups')).read()
        self.assertTrue('%s-dev' % pname in content)

    def test_create_public_project_as_admin_clone_as_user(self):
        """ Create public project as admin then clone as user
        """
        pname = 'p_%s' % create_random_str()
        # create the project as admin
        self.createProject(pname, config.ADMIN_USER, config.ADMIN_PASSWD)
        # add user2 ssh pubkey to user2
        gu = GerritUtil(config.GERRIT_SERVER, username=config.USER_2,
                        password=config.USER_2_PASSWD)
        gu.addPubKey(config.USER_2_PUB_KEY)
        # prepare to clone
        priv_key_path = set_private_key(config.USER_2_PRIV_KEY)
        self.dirs_to_delete.append(os.path.dirname(priv_key_path))
        ggu = GerritGitUtils(config.USER_2,
                             priv_key_path,
                             config.USER_2_EMAIL)
        url = "ssh://%s@%s/%s" % (config.USER_2,
                                  config.GERRIT_HOST, pname)
        # clone
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))

    def test_create_public_project_as_user_clone_as_user(self):
        """ Create public project as user then clone as user
        """
        pname = 'p_%s' % create_random_str()
        # create the project as admin
        self.createProject(pname, config.USER_2, config.USER_2_PASSWD)
        # add user2 ssh pubkey to user2
        gu = GerritUtil(config.GERRIT_SERVER, username=config.USER_2,
                        password=config.USER_2_PASSWD)
        gu.addPubKey(config.USER_2_PUB_KEY)
        # prepare to clone
        priv_key_path = set_private_key(config.USER_2_PRIV_KEY)
        self.dirs_to_delete.append(os.path.dirname(priv_key_path))
        ggu = GerritGitUtils(config.USER_2,
                             priv_key_path,
                             config.USER_2_EMAIL)
        url = "ssh://%s@%s/%s" % (config.USER_2,
                                  config.GERRIT_HOST, pname)
        # clone
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))
