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
from subprocess import Popen, PIPE, call, CalledProcessError

from pysflib.sfgerrit import GerritUtils


class TestProjectReplication(Base):
    """ Functional tests to verify the gerrit replication feature
    """
    def setUp(self):
        super(TestProjectReplication, self).setUp()
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

        # Prepare environment for git clone on mirror repo
        self.mt = Tool()
        self.mt_tempdir = tempfile.mkdtemp()
        # Copy the service private key in a flat file
        priv_key = file(config.SERVICE_PRIV_KEY_PATH, 'r').read()
        priv_key_path = os.path.join(self.mt_tempdir, 'user.priv')
        file(priv_key_path, 'w').write(priv_key)
        os.chmod(priv_key_path, stat.S_IREAD | stat.S_IWRITE)
        # Prepare the ssh wrapper script
        ssh_wrapper = "ssh -o StrictHostKeyChecking=no -i %s \"$@\"" % (
            priv_key_path)
        wrapper_path = os.path.join(self.mt_tempdir, 'ssh_wrapper.sh')
        file(wrapper_path, 'w').write(ssh_wrapper)
        os.chmod(wrapper_path, stat.S_IRWXU)
        # Set the wrapper as GIT_SSH env variable
        self.mt.env['GIT_SSH'] = wrapper_path

        self.config_clone_dir = None

        # Project we are going to configure the replication for
        self.pname = 'test/replication'

        # Remove artifacts of previous run if any
        self.delete_config_section(self.un, self.pname)
        self.delete_mirror_repo(self.pname)

    def tearDown(self):
        super(TestProjectReplication, self).tearDown()
        self.delete_config_section(self.un, self.pname)
        self.delete_mirror_repo(self.pname)
        self.msu.deleteProject(self.pname, self.un)
        self.gu2.del_pubkey(self.k_idx)

    def clone(self, uri, target):
        self.assertTrue(uri.startswith('ssh://'))
        cmd = "git clone %s %s" % (uri, target)
        clone = os.path.join(self.mt_tempdir, target)
        if os.path.isdir(clone):
            shutil.rmtree(clone)
        self.mt.exe(cmd, self.mt_tempdir)
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
        return p.communicate(), p.returncode

    def delete_mirror_repo(self, name):
        mirror_path = '/home/gerrit/git/%s.git' % name
        cmd = ['ssh', 'gerrit.%s' % config.GATEWAY_HOST,
               'rm', '-rf', mirror_path]
        self.ssh_run_cmd(config.SERVICE_PRIV_KEY_PATH,
                         'root',
                         config.GATEWAY_HOST, cmd)

    def create_config_section(self, project):
        host = '%s@%s' % (config.GERRIT_USER, config.GATEWAY_HOST)
        mirror_repo_path = '/home/gerrit/git/\${name}.git'
        url = '%s:%s' % (host, mirror_repo_path)
        path = os.path.join(self.config_clone_dir,
                            'gerrit/replication.config')
        call("git config -f %s --remove-section remote.test_project" %
             path, shell=True)
        call("git config -f %s --add remote.test_project.projects %s" %
             (path, project), shell=True)
        call("git config -f %s --add remote.test_project.url %s" %
             (path, url), shell=True)
        self.gitu_admin.add_commit_for_all_new_additions(
            self.config_clone_dir, "Add replication test section")
        # The direct push will trigger the config-update job
        # as we commit through 29418
        self.gitu_admin.direct_push_branch(self.config_clone_dir, 'master')
        attempts = 0
        cmd = ['ssh', 'gerrit.%s' % config.GATEWAY_HOST, 'grep',
               'test_project', '/home/gerrit/site_path/etc/replication.config']
        while attempts < 30:
            out, code = self.ssh_run_cmd(config.SERVICE_PRIV_KEY_PATH,
                                         'root',
                                         config.GATEWAY_HOST, cmd)
            if code == 0:
                return
            attempts += 1
            time.sleep(2)
        raise Exception('replication.config file has not been updated (add)')

    def delete_config_section(self, user, project):
        url = "ssh://%s@%s:29418/config" % (self.un, config.GATEWAY_HOST)
        self.config_clone_dir = self.gitu_admin.clone(
            url, 'config', config_review=True)
        path = os.path.join(self.config_clone_dir, 'gerrit/replication.config')
        call("git config -f %s --remove-section remote.test_project" %
             path, shell=True)
        try:
            self.gitu_admin.add_commit_for_all_new_additions(
                self.config_clone_dir, "Remove replication test section")
        except CalledProcessError:
            # We fail if nothing to re-initialized
            return
        # The direct push will trigger the config-update job
        # as we commit through 29418
        self.gitu_admin.direct_push_branch(self.config_clone_dir, 'master')
        attempts = 0
        cmd = ['ssh', 'gerrit.%s' % config.GATEWAY_HOST, 'grep',
               'test_project',
               '/home/gerrit/site_path/etc/replication.config']
        while attempts < 30:
            out, code = self.ssh_run_cmd(config.SERVICE_PRIV_KEY_PATH,
                                         'root',
                                         config.GATEWAY_HOST, cmd)
            if code != 0:
                return
            attempts += 1
            time.sleep(2)
        raise Exception('replication.config has not been updated (rm)')

    def mirror_clone_and_check_files(self, url, pname):
        retries = 0
        while True:
            clone = self.clone(url, pname)
            # clone may fail, as mirror repo is not yet ready(i.e gerrit not
            # yet replicated the project)
            if os.path.isdir(clone) and \
               os.path.isfile(os.path.join(clone, '.gitreview')):
                return True
            elif retries > 50:
                break
            else:
                time.sleep(3)
                retries += 1
        return False

    def test_replication(self):
        """ Test gerrit replication for review process
        """
        # Create the project
        self.create_project(self.pname, self.un)

        # Be sure sftests.com host key is inside the known_hosts
        cmds = [['ssh', 'gerrit.%s' % config.GATEWAY_HOST,
                 'ssh-keyscan', 'sftests.com', '>',
                 '/home/gerrit/.ssh/known_hosts']]
        for cmd in cmds:
            self.ssh_run_cmd(config.SERVICE_PRIV_KEY_PATH,
                             'root',
                             config.GATEWAY_HOST, cmd)

        # Create new section for this project in replication.config
        self.create_config_section(self.pname)

        # Verify if gerrit replicated the repo
        self.managesf_repo_path = "ssh://%s@%s/home/gerrit/git/" % (
            'root', config.GATEWAY_HOST)
        repo_url = self.managesf_repo_path + '%s.git' % self.pname
        self.assertTrue(self.mirror_clone_and_check_files(repo_url,
                                                          self.pname))
