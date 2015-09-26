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
from utils import Tool
from subprocess import Popen, PIPE, call

from pysflib.sfgerrit import GerritUtils


class TestProjectReplication(Base):
    """ Functional tests to verify the gerrit replication feature
    """
    def setUp(self):
        self.msu = ManageSfUtils(config.GATEWAY_URL)
        self.un = config.ADMIN_USER
        self.gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[self.un]['auth_cookie'])
        self.gu2 = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.USER_2]['auth_cookie'])
        self.k_idx = self.gu2.add_pubkey(config.USERS[config.USER_2]["pubkey"])
        priv_key_path = set_private_key(config.USERS[self.un]["privkey"])
        self.gitu_admin = GerritGitUtils(self.un,
                                         priv_key_path,
                                         config.USERS[self.un]['email'])
        # Configuration to access mirror repo present in mysql
        self.msql_repo_path = "ssh://%s@%s/%s" \
                              % (config.GERRIT_USER, config.GATEWAY_HOST,
                                 'home/gerrit/site_path/git/')
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
        self.pname = 'test-replication'

    def tearDown(self):
        self.deleteConfigSection(self.un, self.pname)
        self.deleteMirrorRepo(self.pname)
        self.msu.deleteProject(self.pname, self.un)
        self.gu2.del_pubkey(self.k_idx)

    # Can't use GerritGitUtils.clone as not sure when source uri repo in mysql
    # be ready.(i.e gerrit is taking time to create the mirror repo in mysql
    # node) So this clone may succeed or fail, we don't need 'git review -s'
    # and other review commands in clone method
    def clone(self, uri, target):
        self.assertTrue(uri.startswith('ssh://'))
        cmd = "git clone %s %s" % (uri, target)
        self.mt.exe(cmd, self.mt_tempdir)
        clone = os.path.join(self.mt_tempdir, target)
        return clone

    def create_project(self, name, user, options=None):
        self.msu.createProject(name, user, options)

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
        host = config.GATEWAY_HOST
        mirror_path = '/home/gerrit/site_path/git/%s.git' % name
        cmd = ['rm', '-rf', mirror_path]
        self.ssh_run_cmd(sshkey_priv_path, user, host, cmd)

    def createConfigSection(self, user, project):
        # Section name will be node name and the project
        section = 'mysql_%s' % project
        host = '%s@%s' % (config.GERRIT_USER, config.GATEWAY_HOST)
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
            # clone may fail, as mirror repo is not yet ready(i.e gerrit not
            # yet replicated the project)
            if os.path.isdir(clone):
                files = [f for f in os.listdir(clone) if not f.startswith('.')]
                shutil.rmtree(clone)
            if us_files and files:
                break
            elif retries > 30:
                break
            else:
                time.sleep(3)
                retries += 1
        if us_files:
            for f in us_files:
                self.assertIn(f, files)
            self.assertTrue((len(us_files) < len(files)))

    def test_replication(self):
        """ Test gerrit replication for review process
        """
        # Temporary disable this test
        return True
        # Be sure the project, mirror repo, project in config don't exist
        self.deleteMirrorRepo(self.pname)
        self.deleteConfigSection(self.un, self.pname)
        self.msu.deleteProject(self.pname, self.un)

        # Create the project
        self.create_project(self.pname, self.un)

        # Create new section for this project in replication.config
        self.createConfigSection(self.un, self.pname)

        # Force gerrit to read its known_hosts file. The only
        # way to do that is by restarting gerrit. The Puppet Gerrit
        # manifest will restart gerrit if a new entry in known_hosts_gerrit
        # is discovered.
        # This may take some time (gerrit in some condition take long
        # to be fully up)
        call("ssh root@192.168.135.54 systemctl restart gerrit", shell=True)

        # Clone the project and submit it for review
        priv_key_path = set_private_key(config.USERS[self.un]["privkey"])
        gitu = GerritGitUtils(self.un,
                              priv_key_path,
                              config.USERS[self.un]['email'])
        url = "ssh://%s@%s:29418/%s" % (self.un, config.GATEWAY_HOST,
                                        self.pname)
        clone_dir = gitu.clone(url, self.pname)

        gitu.add_commit_and_publish(clone_dir, "master", "Test commit")

        # Add 2 files and resubmit for review
        data = "echo Working"
        us_files = ["run_functional-tests.sh", "run_tests.sh"]

        for f in us_files:
            file(os.path.join(clone_dir, f), 'w').write(data)
            os.chmod(os.path.join(clone_dir, f), 0755)

        gitu.add_commit_and_publish(clone_dir, "master", None, fnames=us_files)

        # Review the patch and merge it
        change_ids = self.gu.get_my_changes_for_project(self.pname)
        self.assertGreater(len(change_ids), 0)
        change_id = change_ids[0]
        self.gu.submit_change_note(change_id, "current", "Code-Review", "2")
        self.gu.submit_change_note(change_id, "current", "Verified", "2")
        self.gu.submit_change_note(change_id, "current", "Workflow", "1")
        # Put USER_2 as core for config project
        grp_name = '%s-core' % self.pname
        self.gu.add_group_member(config.USER_2, grp_name)
        self.gu2.submit_change_note(change_id, "current", "Code-Review", "2")
        self.assertTrue(self.gu.submit_patch(change_id, "current"))
        shutil.rmtree(clone_dir)

        # Verify if gerrit automatically triggered replication
        # Mirror repo(in mysql node) should have these latest changes
        # Clone the mirror repo(from mysql) and check for the 2 files
        msql_repo_url = self.msql_repo_path + '%s.git' % self.pname
        self.mirror_clone_and_check_files(msql_repo_url, self.pname, us_files)
