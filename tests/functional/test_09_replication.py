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
import time
import stat
import tempfile

from utils import Base
from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import GerritUtil, Tool
from subprocess import Popen, PIPE


class TestProjectReplication(Base):
    """ Functional tests to verify the gerrit replication feature
    """
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_HOST, 80)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.un = config.ADMIN_USER
        self.gu = GerritUtil(config.GERRIT_SERVER, username=self.un)
        self.gu2 = GerritUtil(config.GERRIT_SERVER, username=config.USER_2)
        self.k_idx = self.gu2.addPubKey(config.USERS[config.USER_2]["pubkey"])
        priv_key_path = set_private_key(config.USERS[self.un]["privkey"])
        self.gitu_admin = GerritGitUtils(self.un,
                                         priv_key_path,
                                         config.USERS[self.un]['email'])
        # Configuration to access mirror repo present in mysql
        un = config.GERRIT_USER
        self.msql_repo_path = "ssh://%s@%s/%s" \
                              % (un, config.MYSQL_HOST,
                                 '/home/gerrit/site_path/git/')
        # prepare environment for git clone on mirror repo
        self.mt = Tool()
        self.mt_tempdir = tempfile.mkdtemp()
        priv_key = file(config.GERRIT_SERVICE_PRIV_KEY_PATH, 'r').read()
        priv_key_path = os.path.join(self.mt_tempdir, 'user.priv')
        file(priv_key_path, 'w').write(priv_key)
        os.chmod(priv_key_path, stat.S_IREAD | stat.S_IWRITE)
        ssh_wrapper = "ssh -o StrictHostKeyChecking=no -i " \
                      "%s \"$@\"" % priv_key_path
        wrapper_path = os.path.join(self.mt_tempdir, 'ssh_wrapper.sh')
        file(wrapper_path, 'w').write(ssh_wrapper)
        os.chmod(wrapper_path, stat.S_IRWXU)
        self.mt.env['GIT_SSH'] = wrapper_path

#Can't use GerritGitUtils.clone as not sure when source uri repo in mysql be
#ready.(i.e gerrit is taking time to create the mirror repo in mysql node)
#So this clone may succeed or fail, we don't need 'git review -s' and
#other review commands in clone method
    def clone(self, uri, target):
        assert uri.startswith('ssh://')
        print self.mt_tempdir
        cmd = "git clone %s %s" % (uri, target)
        self.mt.exe(cmd, self.mt_tempdir)
        clone = os.path.join(self.mt_tempdir, target)
        return clone

    def tearDown(self):
        self.gu2.delPubKey(self.k_idx)

    def createProject(self, name, user,
                      options=None):
        self.msu.createProject(name, user,
                               options)

    def ssh_run_cmd(self, sshkey_priv_path, user, host, subcmd):
        host = '%s@%s' % (user, host)
        sshcmd = ['ssh', '-o', 'LogLevel=ERROR',
                  '-o', 'StrictHostKeyChecking=no',
                  '-o', 'UserKnownHostsFile=/dev/null', '-i',
                  sshkey_priv_path, host]
        cmd = sshcmd + subcmd

        p = Popen(cmd, stdout=PIPE)
        return p.communicate()

    def deleteMirrorRepo(self, name):
        sshkey_priv_path = config.GERRIT_SERVICE_PRIV_KEY_PATH
        user = 'gerrit'
        host = config.MYSQL_HOST
        mirror_path = '/home/gerrit/site_path/git/%s.git' % name
        cmd = ['rm', '-rf', mirror_path]
        self.ssh_run_cmd(sshkey_priv_path, user, host, cmd)

    def createConfigSection(self, user, project):
        # Section name will be node name and the project
        section = 'mysql_%s' % project
        host = '%s@%s' % (config.GERRIT_USER, config.MYSQL_HOST)
        mirror_repo_path = '/home/gerrit/site_path/git/\${name}.git'
        url = '%s:%s' % (host, mirror_repo_path)
        self.msu.replicationModifyConfig(user, 'add', section,
                                         'projects', project)
        self.msu.replicationModifyConfig(user, 'add',
                                         section, 'url', url)
        push = '+refs/heads/*:refs/heads/*'
        self.msu.replicationModifyConfig(user, 'add',
                                         section, 'push', push)
        push = '+refs/tags/*:refs/tags/*'
        self.msu.replicationModifyConfig(user, 'add',
                                         section, 'push', push)

    def deleteConfigSection(self, user, project):
        # section name will be node name and the project
        section = 'managesf_%s' % project
        self.msu.replicationModifyConfig(user, 'remove-section', section)

    def mirror_clone_and_check_files(self, url, pname, us_files):
        retries = 0
        files = []
        while True:
            clone = self.clone(url, pname)
            #clone may fail, as mirror repo is not yet ready(i.e gerrit not
            #yet replicated the project)
            if os.path.isdir(clone):
                files = [f for f in os.listdir(clone) if not f.startswith('.')]
                shutil.rmtree(clone)
            if us_files and files:
                print files
                break
            elif retries > 30:
                break
            else:
                time.sleep(3)
                retries += 1
        if us_files:
            for f in us_files:
                self.assertIn(f, files)
            assert (len(us_files) < len(files))

    def test_replication(self):
        """ Test gerrit replication for review process
        """
        pname = 'test-replication'
        un = config.ADMIN_USER
        # Be sure the project, mirror repo, project in config don't exist
        self.deleteMirrorRepo(pname)
        self.deleteConfigSection(un, pname)
        self.msu.deleteProject(pname,
                               config.ADMIN_USER)

        # Create the project
        self.createProject(pname, config.ADMIN_USER)

        # Create new section for this project in replication.config
        self.createConfigSection(un, pname)
        time.sleep(5)

        # Trigger the replication
        self.msu.replicationTrigger(un, pname)
        time.sleep(5)

        # Clone the project and submit it for review
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s/%s" % (un, config.GERRIT_HOST,
                                  pname)
        clone_dir = gitu.clone(url, pname)

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")

        # Add 2 files and resubmit for review
        data = "echo Working"
        us_files = ["run_functional-tests.sh", "run_tests.sh"]

        for f in us_files:
            file(os.path.join(clone_dir, f), 'w').write(data)
            os.chmod(os.path.join(clone_dir, f), 0755)

        gitu.add_commit_and_publish(clone_dir, "master", None, fnames=us_files)

        # Review the patch and merge it
        change_ids = self.gu.getMyChangesForProject(pname)
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]
        self.gu.setPlus2CodeReview(change_id, "current")
        self.gu.setPlus1Verified(change_id, "current")
        self.gu.setPlus1Approved(change_id, "current")
        # Put USER_2 as core for config project
        grp_name = '%s-core' % pname
        self.gu.addGroupMember(config.USER_2, grp_name)
        self.gu2.setPlus2CodeReview(change_id, "current")
        self.assertEqual(
            self.gu.submitPatch(change_id, "current")['status'], 'MERGED')
        shutil.rmtree(clone_dir)

        time.sleep(5)
        # Verify if gerrit automatically triggered replication
        # Mirror repo(in mysql node) should have these latest changes
        # Clone the mirror repo(from mysql) and check for the 2 files
        msql_repo_url = self.msql_repo_path + '%s.git' % pname
        self.mirror_clone_and_check_files(msql_repo_url, pname, us_files)

        # delete project and mirror repo
        self.deleteConfigSection(un, pname)
        self.deleteMirrorRepo(pname)
        self.msu.deleteProject(pname, config.ADMIN_USER)
