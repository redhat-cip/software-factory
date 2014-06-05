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
import yaml

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
        with open(os.environ['SF_ROOT'] + "/build/hiera/redmine.yaml") as f:
            ry = yaml.load(f)
        cls.redmine_api_key = ry['redmine']['issues_tracker_api_key']

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.dirs_to_delete = []
        self.rm = RedmineUtil(config.REDMINE_SERVER,
                              apiKey=self.redmine_api_key)
        self.gu = GerritUtil(config.GERRIT_SERVER,
                             username=config.ADMIN_USER)

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def createProject(self, name, user,
                      options=None):
        self.msu.createProject(name, user,
                               options)
        self.projects.append(name)

    def test_create_public_project_as_admin(self):
        """ Create public project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER)
        # Gerrit part
        assert self.gu.isPrjExist(pname)
        assert self.gu.isGroupExist('%s-ptl' % pname)
        assert self.gu.isGroupExist('%s-core' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-core' % pname)
        # Redmine part
        assert self.rm.isProjectExist(pname)
        assert self.rm.checkUserRole(pname, config.ADMIN_USER, 'Manager')
        assert self.rm.checkUserRole(pname, config.ADMIN_USER, 'Developer')
        # Test here the project is public
        # ( Redmine API project detail does not return this flag)
        assert self.rm.isProjectExist_ex(pname, config.USER_2)

    def test_create_private_project_as_admin(self):
        """ Create private project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        options = {"private": ""}
        self.createProject(pname, config.ADMIN_USER,
                           options=options)
        # Gerrit part
        assert self.gu.isPrjExist(pname)
        assert self.gu.isGroupExist('%s-ptl' % pname)
        assert self.gu.isGroupExist('%s-core' % pname)
        assert self.gu.isGroupExist('%s-dev' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-core' % pname)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-dev' % pname)
        # Redmine part
        assert self.rm.isProjectExist(pname)
        assert self.rm.checkUserRole(pname, config.ADMIN_USER, 'Manager')
        assert self.rm.checkUserRole(pname, config.ADMIN_USER, 'Developer')
        # Test here the project is private
        # ( Redmine API project detail does not return this flag)
        assert not self.rm.isProjectExist_ex(pname, config.USER_2)

    def test_delete_public_project_as_admin(self):
        """ Delete public project on redmine and gerrit as admin
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER)
        assert self.gu.isPrjExist(pname)
        assert self.rm.isProjectExist(pname)
        self.msu.deleteProject(pname, config.ADMIN_USER)
        assert not self.gu.isPrjExist(pname)
        assert not self.gu.isGroupExist('%s-ptl' % pname)
        assert not self.rm.isProjectExist(pname)
        assert not self.gu.isGroupExist('%s-core' % pname)
        self.projects.remove(pname)

    def test_create_public_project_as_user(self):
        """ Create public project on redmine and gerrit as user
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.USER_2)
        # Gerrit part
        assert self.gu.isPrjExist(pname)
        assert self.gu.isGroupExist('%s-ptl' % pname)
        assert self.gu.isGroupExist('%s-core' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-core' % pname)
        # Redmine part
        assert self.rm.isProjectExist(pname)
        assert self.rm.isProjectExist_ex(pname, config.USER_2)
        assert self.rm.checkUserRole(pname, config.USER_2, 'Manager')
        assert self.rm.checkUserRole(pname, config.USER_2, 'Developer')
        # Test here the project is public
        # ( Redmine API project detail does not return this flag)
        assert self.rm.isProjectExist_ex(pname, config.USER_3)

    def test_create_private_project_as_user(self):
        """ Create private project on redmine and gerrit as user
        """
        pname = 'p_%s' % create_random_str()
        options = {"private": ""}
        self.createProject(pname, config.USER_2,
                           options=options)
        # Gerrit part
        assert self.gu.isPrjExist(pname)
        assert self.gu.isGroupExist('%s-ptl' % pname)
        assert self.gu.isGroupExist('%s-core' % pname)
        assert self.gu.isGroupExist('%s-dev' % pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert self.gu.isMemberInGroup(config.USER_2, '%s-ptl' % pname)
        assert self.gu.isMemberInGroup(config.USER_2, '%s-core' % pname)
        assert self.gu.isMemberInGroup(config.USER_2, '%s-dev' % pname)
        # Redmine part
        assert self.rm.isProjectExist(pname)
        assert self.rm.isProjectExist_ex(pname, config.USER_2)
        assert self.rm.checkUserRole(pname, config.USER_2, 'Manager')
        assert self.rm.checkUserRole(pname, config.USER_2, 'Developer')
        # Test here the project is private
        # ( Redmine API project detail does not return this flag)
        assert not self.rm.isProjectExist_ex(pname, config.USER_3)

    def test_create_public_project_with_users_in_group(self):
        """ Create public project on redmine and gerrit with users in groups
        """
        pname = 'p_%s' % create_random_str()
        options = {"ptl-group": "",
                   "core-group": "%s,%s" % (config.USER_2, config.USER_3),
                   }
        self.createProject(pname, config.ADMIN_USER,
                           options=options)
        # Gerrit part
        assert self.gu.isPrjExist(pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        for user in (config.ADMIN_USER, config.USER_2, config.USER_3):
            assert self.gu.isMemberInGroup(user, '%s-core' % pname)
        # Redmine part
        assert self.rm.isProjectExist(pname)
        assert self.rm.checkUserRole(pname, config.ADMIN_USER, 'Manager')
        for user in (config.ADMIN_USER, config.USER_2, config.USER_3):
            assert self.rm.checkUserRole(pname, user, 'Developer')

    def test_create_private_project_with_users_in_group(self):
        """ Create private project on redmine and gerrit with users in groups
        """
        pname = 'p_%s' % create_random_str()
        options = {"private": "",
                   "ptl-group": "",
                   "core-group": "%s,%s" % (config.USER_2, config.USER_3),
                   "dev-group": "%s" % (config.USER_4),
                   }
        self.createProject(pname, config.ADMIN_USER,
                           options=options)
        # Gerrit part
        assert self.gu.isPrjExist(pname)
        #TODO(Project creator, as project owner, should only be in ptl group)
        assert self.gu.isMemberInGroup(config.ADMIN_USER, '%s-ptl' % pname)
        for user in (config.ADMIN_USER, config.USER_2, config.USER_3):
            assert self.gu.isMemberInGroup(user, '%s-core' % pname)
        assert self.gu.isMemberInGroup(config.USER_4, '%s-dev' % pname)
        # Redmine part
        assert self.rm.isProjectExist(pname)  # it should be visible to admin
        assert self.rm.checkUserRole(pname, config.ADMIN_USER, 'Manager')
        for user in (config.ADMIN_USER, config.USER_2,
                     config.USER_3, config.USER_4):
            assert self.rm.checkUserRole(pname, user, 'Developer')

    def test_create_public_project_as_admin_clone_as_admin(self):
        """ Clone public project as admin and check content
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname, config.ADMIN_USER)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
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
        options = {"private": ""}
        self.createProject(pname, config.ADMIN_USER, options=options)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
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
        self.createProject(pname, config.ADMIN_USER)
        # add user2 ssh pubkey to user2
        gu = GerritUtil(config.GERRIT_SERVER, username=config.USER_2)
        gu.addPubKey(config.USER_2_PUB_KEY)
        # prepare to clone
        priv_key_path = set_private_key(config.USER_2_PRIV_KEY)
        self.dirs_to_delete.append(os.path.dirname(priv_key_path))
        ggu = GerritGitUtils(config.USER_2,
                             priv_key_path,
                             config.USERS[config.USER_2]['email'])
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
        self.createProject(pname, config.USER_2)
        # add user2 ssh pubkey to user2
        gu = GerritUtil(config.GERRIT_SERVER, username=config.USER_2)
        gu.addPubKey(config.USER_2_PUB_KEY)
        # prepare to clone
        priv_key_path = set_private_key(config.USER_2_PRIV_KEY)
        self.dirs_to_delete.append(os.path.dirname(priv_key_path))
        ggu = GerritGitUtils(config.USER_2,
                             priv_key_path,
                             config.USERS[config.USER_2]['email'])
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

    def test_upstream(self):
        """ Validate upstream feature of managesf
        """
        # Create a test upstream project
        pname_us = 'p_%s' % 'upstream'
        self.createProject(pname_us, config.ADMIN_USER)

        ggu_us = GerritGitUtils(config.ADMIN_USER,
                                config.ADMIN_PRIV_KEY_PATH,
                                config.USERS[config.ADMIN_USER]['email'])
        url = "ssh://%s@%s/%s" % (config.ADMIN_USER,
                                  config.GERRIT_HOST, pname_us)
        # clone
        us_clone_dir = ggu_us.clone(url, pname_us)
        self.dirs_to_delete.append(os.path.dirname(us_clone_dir))
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(us_clone_dir))
        # push some test files to the upstream project
        us_files = [str(x) for x in range(1, 10)]
        for f in us_files:
            file(os.path.join(us_clone_dir, f), 'w').write(f)
            os.chmod(os.path.join(us_clone_dir, f), 0755)

        ggu_us.add_commit_in_branch(us_clone_dir, "master",
                                    commit="Adding files 1-10",
                                    files=us_files)
        ggu_us.direct_push_branch(us_clone_dir, "master")

        # No create a test project with upstream pointing to the above
        upstream_url = config.GERRIT_SERVER + pname_us
        pname = 'p_%s' % create_random_str()
        # create the project as admin
        options = {"upstream": upstream_url}
        self.createProject(pname, config.ADMIN_USER, options=options)

        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
        url = "ssh://%s@%s/%s" % (config.ADMIN_USER,
                                  config.GERRIT_HOST, pname)
        # clone
        clone_dir = ggu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        # Check if the files pushed in upstream project is present
        files = [f for f in os.listdir(clone_dir) if not f.startswith('.')]
        assert set(files) == set(us_files)
