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
from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import create_random_str
from utils import GerritUtil


class TestGerrit(Base):
    """ Functional tests that validate some gerrit behaviors.
    """
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.clone_dirs = []
        self.dirs_to_delete = []
        self.msu = ManageSfUtils(config.MANAGESF_HOST, 80)

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)
        for dirs in self.dirs_to_delete:
            shutil.rmtree(dirs)

    def createProject(self, name, options=None):
        self.msu.createProject(name,
                               config.ADMIN_USER,
                               options=options)
        self.projects.append(name)

    def test_add_remove_user_in_core_as_admin(self):
        """ Add/remove user from core group as admin
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER)
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        assert gu.isPrjExist(pname)
        NEW_USER = 'user2'
        GROUP_NAME = '%s-core' % pname
        assert gu.isGroupExist(GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.addGroupMember(NEW_USER, GROUP_NAME)
        assert gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.deleteGroupMember(NEW_USER, GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)

    def test_add_remove_user_in_ptl_as_admin(self):
        """ Add/remove user from ptl group as admin
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER)
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        assert gu.isPrjExist(pname)
        NEW_USER = 'user2'
        GROUP_NAME = '%s-ptl' % pname
        assert gu.isGroupExist(GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.addGroupMember(NEW_USER, GROUP_NAME)
        assert gu.isMemberInGroup(NEW_USER, GROUP_NAME)
        gu.deleteGroupMember(NEW_USER, GROUP_NAME)
        assert not gu.isMemberInGroup(NEW_USER, GROUP_NAME)

    def test_review_labels(self):
        """ Test if list of review labels are as expected
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        un = config.ADMIN_USER
        gu = GerritUtil(config.GERRIT_SERVER, username=un)
        hostkey = file("%s/.ssh/id_rsa.pub" % os.environ['HOME']).read()
        hk_index = gu.addPubKey(hostkey)
        k_index = gu.addPubKey(config.USERS[un]["pubkey"])
        assert gu.isPrjExist(pname)
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s/%s" % (un, config.GERRIT_HOST,
                                  pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")
        changes = gu.rest.get('/a/changes/')

        count = 0
        change = None
        for x in changes:
            if x['project'] == pname:
                count += 1
                change = x

        assert count == 1

        change_id = change['change_id']
        url = '/a/changes/%s/?o=LABELS' % change_id
        labels = gu.rest.get(url)['labels']

        assert 'Approved' in labels
        assert 'Code-Review' in labels
        assert 'Verified' in labels
        assert len(labels.keys()) is 3

        gu.delPubKey(hk_index)
        gu.delPubKey(k_index)

    def test_review_submit_approval(self):
        """ Test submit criteria - CR(2 +2s), V(+1), A(+1)
        """
        pname = 'p_%s' % create_random_str()
        options = {'core-group': 'user2'}
        self.createProject(pname, options)
        un = config.ADMIN_USER
        gu = GerritUtil(config.GERRIT_SERVER, username=un)
        hostkey = file("%s/.ssh/id_rsa.pub" % os.environ['HOME']).read()
        hk_index = gu.addPubKey(hostkey)
        k_index = gu.addPubKey(config.USERS[un]["pubkey"])
        assert gu.isPrjExist(pname)
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s/%s" % (un, config.GERRIT_HOST,
                                  pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")
        changes = gu.rest.get('/a/changes/')
        count = 0
        change = None
        for x in changes:
            if x['project'] == pname:
                count += 1
                change = x

        assert count == 1

        change_id = change['change_id']

        gu.setPlus1CodeReview(change_id, "current")
        assert gu.submitPatch(change_id, "current") == 409

        gu.setPlus1Verified(change_id, "current")
        assert gu.submitPatch(change_id, "current") == 409

        gu.setPlus1Approved(change_id, "current")
        assert gu.submitPatch(change_id, "current") == 409

        gu.setPlus2CodeReview(change_id, "current")
        assert gu.submitPatch(change_id, "current") == 409

        gu_user2 = GerritUtil(config.GERRIT_SERVER, username=config.USER_2)
        gu_user2.setPlus2CodeReview(change_id, "current")
        assert gu.submitPatch(change_id, "current")['status'] == 'MERGED'
        gu.delPubKey(hk_index)
        gu.delPubKey(k_index)

    def test_ifexist_download_commands(self):
        """ Test if download-commands plugin is present
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER)
        plugins = gu.listPlugins()
        assert 'download-commands' in plugins

    def test_ifexist_gravatar(self):
        """ Test if gravatar plugin is present
        """
        gu = GerritUtil(config.GERRIT_SERVER, username=config.ADMIN_USER)
        plugins = gu.listPlugins()
        assert 'gravatar-avatar-provider' in plugins

    def test_check_download_commands(self):
        """ Test if download commands plugin works
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        un = config.ADMIN_USER
        gu = GerritUtil(config.GERRIT_SERVER, username=un)
        hostkey = file("%s/.ssh/id_rsa.pub" % os.environ['HOME']).read()
        hk_index = gu.addPubKey(hostkey)
        k_index = gu.addPubKey(config.USERS[un]["pubkey"])
        assert gu.isPrjExist(pname)
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s/%s" % (un, config.GERRIT_HOST,
                                  pname)
        clone_dir = gitu.clone(url, pname)
        self.dirs_to_delete.append(os.path.dirname(clone_dir))

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")
        changes = gu.rest.get('/a/changes/')
        count = 0
        change = None
        for x in changes:
            if x['project'] == pname:
                count += 1
                change = x

        assert count == 1

        change_id = change['change_id']
        resp = gu.rest.get('/a/changes/%s/?o=CURRENT_REVISION' % change_id)
        assert "current_revision" in resp
        assert "revisions" in resp

        current_rev = resp["current_revision"]

        fetch = resp["revisions"][current_rev]["fetch"]
        assert len(fetch.keys()) > 0

        # disable and check if the fetch has anything
        gu.disablePlugin("download-commands")
        resp = gu.rest.get('/a/changes/%s/?o=CURRENT_REVISION' % change_id)
        fetch = resp["revisions"][current_rev]["fetch"]
        assert len(fetch.keys()) is 0

        # enable the plugin and check if the fetch information is valid
        gu.enablePlugin("download-commands")
        resp = gu.rest.get('/a/changes/%s/?o=CURRENT_REVISION' % change_id)
        fetch = resp["revisions"][current_rev]["fetch"]
        assert len(fetch.keys()) > 0

        gu.delPubKey(hk_index)
        gu.delPubKey(k_index)
