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
import unittest
import subprocess
import shlex
import stat
import config
import tempfile
import string
import random
import json
import requests as http
from redmine import Redmine
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from pygerrit import rest


def create_random_str():
    value = "".join([random.choice(string.ascii_lowercase) for _ in range(6)])
    return value


def set_private_key(priv_key):
    tempdir = tempfile.mkdtemp()
    priv_key_path = os.path.join(tempdir, 'user.priv')
    file(priv_key_path, 'w').write(priv_key)
    os.chmod(priv_key_path, stat.S_IREAD | stat.S_IWRITE)
    return priv_key_path


class Base(unittest.TestCase):
    pass


class Tool:
    def __init__(self):
        self.debug = file('/tmp/debug', 'a')
        self.env = os.environ.copy()

    def exe(self, cmd, cwd=None, wait=True):
        cmd = shlex.split(cmd)
        ocwd = os.getcwd()
        if cwd:
            os.chdir(cwd)
        try:
            p = subprocess.Popen(cmd, stdout=self.debug,
                                 stderr=subprocess.STDOUT,
                                 env=self.env)
            if wait:
                p.wait()
        finally:
            os.chdir(ocwd)
        return p


class ManageSfUtils(Tool):
    def __init__(self, host, port):
        Tool.__init__(self)
        self.host = host
        self.port = port
        self.install_dir = "tools/managesf/cli"
        self.base_cmd = \
            "python sf-manage.py --host %s --port %s --auth %%s:%%s " \
            % (self.host, self.port)

    def createProject(self, name, user, options=None):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + "create --name %s" % name
        if options:
            for k, v in options.items():
                cmd = cmd + " --" + k + " " + v

        self.exe(cmd, self.install_dir)

    def deleteProject(self, name, user):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + "delete --name %s" % name
        self.exe(cmd, self.install_dir)


class ManageSfUtilsConfigCreator(Tool):
    def __init__(self):
        Tool.__init__(self)
        self.install_dir = "tools/managesf/utils"

    def createConfigProject(self):
        cmd = "bash init-config-repo.sh"
        self.exe(cmd, self.install_dir)

    def deleteProject(self, user):
        passwd = config.USERS[user]['password']
        msu = ManageSfUtils(config.MANAGESF_HOST, 80)
        msu.deleteProject('config', user, passwd)


class GerritGitUtils(Tool):
    def __init__(self, user, priv_key_path, email):
        Tool.__init__(self)
        self.user = user
        self.email = "%s <%s>" % (self.user, email)
        self.priv_key_path = priv_key_path
        self.tempdir = tempfile.mkdtemp()
        ssh_wrapper = "ssh -o StrictHostKeyChecking=no -i " \
                      "%s \"$@\"" % self.priv_key_path
        wrapper_path = os.path.join(self.tempdir, 'ssh_wrapper.sh')
        file(wrapper_path, 'w').write(ssh_wrapper)
        os.chmod(wrapper_path, stat.S_IRWXU)
        self.env['GIT_SSH'] = wrapper_path
        self.env['GIT_COMMITTER_NAME'] = self.user
        self.env['GIT_COMMITTER_EMAIL'] = self.email

    def clone(self, uri, target):
        assert uri.startswith('ssh://')
        cmd = "git clone %s %s" % (uri, target)
        self.exe(cmd, self.tempdir)
        clone = os.path.join(self.tempdir, target)
        assert os.path.isdir(clone)
        return clone

    def fetch_meta_config(self, clone_dir):
        cmd = 'git fetch origin' \
            ' refs/meta/config:refs/remotes/origin/meta/config'
        self.exe(cmd, clone_dir)
        self.exe('git checkout meta/config', clone_dir)

    def add_commit_in_branch(self, clone_dir, branch):
        self.exe('git checkout master', clone_dir)
        self.exe('git checkout -b %s' % branch)
        file(os.path.join(clone_dir, 'testfile'), 'w').write('data')
        self.exe('git add testfile', clone_dir)
        self.exe("git commit --author '%s' testfile" % self.email, clone_dir)

    def direct_push_branch(self, clone_dir, branch):
        self.exe('git checkout %s' % branch, clone_dir)
        self.exe('git push origin %s' % branch, clone_dir)
        self.exe('git checkout master', clone_dir)

    def review_push_branch(self, clone_dir, branch):
        self.exe('git checkout %s' % branch, clone_dir)
        self.exe('git review' % clone_dir)
        self.exe('git checkout master', clone_dir)


class GerritUtil:
    def __init__(self, url, username=None):
        password = config.USERS[username]['password'] if username else None
        self.url = url
        self.username = username
        self.password = password
        self.auth = None
        self.anonymous = False
        if username is None or password is None:
            self.anonymous = True
        if not self.anonymous:
            self.auth = HTTPBasicAuth(username, password)
        # The original SUFFIX does not fit well with our
        # installation of Gerrit
        rest.GERRIT_AUTH_SUFFIX = ''
        self.rest = rest.GerritRestAPI(self.url, self.auth)

    # project APIs
    def getProjects(self, name=None):
        if name:
            return self.rest.get('/a/projects/%s' % name)
        else:
            return self.rest.get('/a/projects/?')

    def isPrjExist(self, name):
        try:
            p = self.getProjects(name)
            return p['name'] == name
        except HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise

    # Group APIs
    def isGroupExist(self, name):
        g = self.rest.get('/a/groups/')
        return name in g

    def getGroupOwner(self, name):
        g = self.rest.get('/a/groups/%s/owner' % name)
        return g['owner']

    def isMemberInGroup(self, username, groupName):
        try:
            g = self.rest.get('/a/groups/%s/members/%s' % (groupName,
                                                           username))
            return (len(g) >= 1 and g['username'] == username)
        except HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise

    def addGroupMember(self, username, groupName):
        self.rest.put('/a/groups/%s/members/%s' % (groupName, username))

    def deleteGroupMember(self, username, groupName):
        self.rest.delete('/a/groups/%s/members/%s' % (groupName, username))

    def addPubKey(self, pubkey):
        headers = {'content-type': 'plain/text'}
        self.rest.post('/a/accounts/self/sshkeys',
                       data=pubkey,
                       headers=headers)

    # Review APIs
    def _submitCodeReview(self, change_id, revision_id, rate):
        reviewInput = {"labels": {"Code-Review": int(rate)}}
        self.rest.post('/a/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput)

    def setPlus2CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '+2')

    def setPlus1CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '+1')

    def setMinus2CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '-2')

    def setMinus1CodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '-1')

    def setNoScoreCodeReview(self, change_id, revision_id):
        self._submitCodeReview(change_id, revision_id, '0')

    def _submitVerified(self, change_id, revision_id, rate):
        reviewInput = {"labels": {"Verified": int(rate)}}
        self.rest.post('/a/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput)

    def setPlus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '+1')

    def setMinus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '-1')

    def setNoScoreVerified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '0')


class RedmineUtil:
    def __init__(self, url, username=None, apiKey=None):
        password = config.USERS[username]['password'] if username else None
        self.api_key = apiKey
        if apiKey is not None:
            self.redmine = Redmine(url, key=apiKey)
        elif username is not None and password is not None:
            self.redmine = Redmine(url, username=username, password=password)
        else:
            self.redmine = Redmine(url)

    def isProjectExist(self, name):
        url = "%(redmine_server)s/projects/%(prj_name)s.json" % \
              {"redmine_server": config.REDMINE_SERVER,
               "prj_name": name}
        headers = {"X-Redmine-Api-Key": self.api_key}
        resp = http.get(url, headers=headers)
        if resp.status_code == 200:
            return True

        return False

    def isProjectExist_ex(self, name, username):
        password = config.USERS[username]['password']
        url = "%(redmine_server)s/projects/%(prj_name)s.json" % \
              {"redmine_server": config.REDMINE_SERVER,
               "prj_name": name}
        resp = http.get(url, auth=HTTPBasicAuth(username, password))
        if resp.status_code == 200:
            return True

        return False

    def isIssueInProgress(self, issueId):
        return self.redmine.issues[issueId].status.id is 2

    def isIssueClosed(self, issueId):
        return self.redmine.issues[issueId].status.id is 5

    def createUser(self, username, lastname='None'):
        email = config.USERS[username]['email']
        password = config.USERS[username]['password']

        user = {"login":  username,
                "firstname": username,
                "lastname": lastname,
                "mail": email,
                "password": password
                }
        data = json.dumps({"user": user})
        url = "%(redmine_server)s/users.json" % \
              {"redmine_server": config.REDMINE_SERVER}
        headers = {"X-Redmine-API-Key": self.api_key,
                   "Content-type": "application/json"}
        resp = http.post(url, data=data, headers=headers)

        def current_user_id():
            url = "%(redmine_server)s/users/current.json" % \
                  {"redmine_server": config.REDMINE_SERVER}
            r = http.get(url, auth=HTTPBasicAuth(username, password))
            if r.status_code != 200:
                return None

            return r.json()['user']['id']

        if resp.status_code != 201:
            if resp.status_code == 422:
                return current_user_id()
            return None

        ret = resp.json()
        return ret['user']['id']

    def checkUserRole(self, prj_name, user_id, role_name):
        url = "%(redmine_server)s/projects/%(project)s/memberships.json" % \
              {"redmine_server": config.REDMINE_SERVER,
                  "project": prj_name}
        headers = {"X-Redmine-API-Key": self.api_key}
        resp = http.get(url, headers=headers)
        if resp.status_code != 200:
            return False

        j = resp.json()
        for m in j['memberships']:
            if m['user']['id'] == user_id:
                for r in m['roles']:
                    if r['name'] == role_name:
                        return True

        return False

    def deleteUser(self, user_id):
        url = "%(redmine_server)s/%(user_id)s.xml" % \
              {"redmine_server": config.REDMINE_SERVER,
               "user_id": user_id}

        headers = {"X-Redmine-API-Key": self.api_key}
        resp = http.delete(url, headers=headers)
        if resp.status_code == 200:
            return True

        return False
