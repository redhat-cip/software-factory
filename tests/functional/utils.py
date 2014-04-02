#!/usr/bin/python

import os
import unittest
import subprocess
import shlex
import stat
import tempfile
import time
from multiprocessing import Process
from redmine import Redmine
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from pygerrit.rest import GerritRestAPI


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

class ManageRestServer(Tool):
    def __init__(self):
        Tool.__init__(self)
        self.install_dir = "tools/managesf-ng/"
        self.cmd = "pecan serve config.py"

    def run(self):
        self.env['PYTHONPATH'] = '.'
        self.p = self.exe(self.cmd, self.install_dir, False)
        time.sleep(2)

    def stop(self):
        self.p.terminate()


class ManageSfUtils(Tool):
    def __init__(self, host, port):
        Tool.__init__(self)
        self.host = host
        self.port = port
        self.install_dir = "tools/managesf-ng/cli"
        self.base_cmd = "python sf-manage.py --host %s --port %s --auth %%s:%%s " \
            % (self.host, self.port)

    def createProject(self, name, user, passwd):
        cmd = self.base_cmd % (user, passwd) + "create --name %s" % name
        print cmd
        self.exe(cmd, self.install_dir)

    def deleteProject(self, name, user, passwd):
        cmd = self.base_cmd % (user, passwd) + "delete --name %s" % name
        self.exe(cmd, self.install_dir)


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
    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        self.auth = None
        self.anonymous = False
        if username is None or password is None:
            self.anonymous = True
        if not self.anonymous:
            self.auth = HTTPBasicAuth(username, password)
        self.rest = GerritRestAPI(self.url, self.auth)

    # project APIs
    def getProjects(self, name=None):
        if name:
            return self.rest.get('/projects/%s' % name)
        else:
            return self.rest.get('/projects/?')

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
        g = self.rest.get('/groups/')
        return name in g

    def getGroupOwner(self, name):
        g = self.rest.get('/groups/%s/owner' % name)
        return g['owner']

    def isMemberInGroup(self, username, groupName):
        try:
            g = self.rest.get('/groups/%s/members/%s' % (groupName, username))
            return (len(g) >= 1 and g['username'] == username)
        except HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise

    def addGroupMember(self, username, groupName):
        self.rest.put('/groups/%s/members/%s' % (groupName, username))

    def deleteGroupMember(self, username, groupName):
        self.rest.delete('/groups/%s/members/%s' % (groupName, username))

    # Review APIs
    def _submitCodeReview(self, change_id, revision_id, rate):
        reviewInput = {"labels": {"Code-Review": int(rate)}}
        self.rest.post('/changes/%s/revisions/%s/review' %
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
        self.rest.post('/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput)

    def setPlus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '+1')

    def setMinus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '-1')

    def setNoScoreVerified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '0')


class RedmineUtil:
    def __init__(self, url, username=None, password=None, apiKey=None):
        if apiKey is not None:
            self.redmine = Redmine(url, key=apiKey)
        elif username is not None and password is not None:
            self.redmine = Redmine(url, username=username, password=password)
        else:
            self.redmine = Redmine(url)

    def isProjectExist(self, name):
        for p in self.redmine.projects:
            if p.name == name:
                return True
        return False

    def isIssueInProgress(self, issueId):
        return self.redmine.issues[issueId].status.id is 2

    def isIssueClosed(self, issueId):
        return self.redmine.issues[issueId].status.id is 5
