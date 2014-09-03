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
import shutil
import stat
import tempfile
import string
import random
import json
import requests as http
import config
import requests
import time
import yaml
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from pygerrit.rest import _decode_response

# Empty job for jenkins
EMPTY_JOB_XML = """<?xml version='1.0' encoding='UTF-8'?>
<project>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class='jenkins.scm.NullSCM'/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class='vector'/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""


def create_random_str():
    value = "".join([random.choice(string.ascii_lowercase) for _ in range(6)])
    return value


def set_private_key(priv_key):
    tempdir = tempfile.mkdtemp()
    priv_key_path = os.path.join(tempdir, 'user.priv')
    file(priv_key_path, 'w').write(priv_key)
    os.chmod(priv_key_path, stat.S_IREAD | stat.S_IWRITE)
    return priv_key_path


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def get_cookie(username, password):
    url = "http://%(auth_url)s/auth/login" % {'auth_url': config.GATEWAY_HOST}
    resp = requests.post(url, params={'username': username,
                                      'password': password,
                                      'back': '/'},
                         allow_redirects=False)
    return resp.cookies.get('auth_pubtkt')


class Base(unittest.TestCase):
    pass


class Tool:
    def __init__(self):
        self.debug = file('/tmp/debug', 'a')
        self.env = os.environ.copy()

    def exe(self, cmd, cwd=None):
        self.debug.write("\n\ncmd = %s\n" % cmd)
        self.debug.flush()
        cmd = shlex.split(cmd)
        ocwd = os.getcwd()
        if cwd:
            os.chdir(cwd)
        try:
            p = subprocess.Popen(cmd, stdout=self.debug,
                                 stderr=subprocess.STDOUT,
                                 env=self.env)
            p.wait()
        finally:
            os.chdir(ocwd)
        return p


class ManageSfUtils(Tool):
    def __init__(self, host, port=80):
        Tool.__init__(self)
        self.host = host
        self.port = port
        self.install_dir = os.path.join(os.environ['SF_ROOT'],
                                        "tools/managesf/cli")
        self.base_cmd = "python sf-manage.py --host %s --auth-server " \
            "%s --port %s --auth %%s:%%s " % \
            (self.host, config.GATEWAY_HOST, self.port)

    def createProject(self, name, user, options=None, cookie=None):
        passwd = config.USERS[user]['password']
        base_cmd = self.base_cmd % (user, passwd)
        if cookie:
            base_cmd = base_cmd + "--cookie %s " % (cookie)

        cmd = base_cmd + "create --name %s" % name
        if options:
            for k, v in options.items():
                cmd = cmd + " --" + k + " " + v

        self.exe(cmd, self.install_dir)

    def deleteProject(self, name, user):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + "delete --name %s" % name
        self.exe(cmd, self.install_dir)

    def replicationModifyConfig(self, user, cmd, section,
                                setting=None, value=None):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) \
            + " replication_config %s --section %s " % (cmd, section)
        if setting:
            cmd = cmd + " " + setting
        if value:
            cmd = cmd + " " + value
        self.exe(cmd, self.install_dir)

    def replicationTrigger(self, user, project=None, url=None):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + " trigger_replication "
        if project:
            cmd = cmd + " --project " + project
        if url:
            cmd = cmd + " --url " + url
        self.exe(cmd, self.install_dir)


class GerritGitUtils(Tool):
    def __init__(self, user, priv_key_path, email):
        Tool.__init__(self)
        self.user = user
        self.email = email
        self.author = "%s <%s>" % (self.user, email)
        self.priv_key_path = priv_key_path
        self.tempdir = tempfile.mkdtemp()
        ssh_wrapper = "ssh -o StrictHostKeyChecking=no -i " \
                      "%s \"$@\"" % os.path.abspath(self.priv_key_path)
        wrapper_path = os.path.join(self.tempdir, 'ssh_wrapper.sh')
        file(wrapper_path, 'w').write(ssh_wrapper)
        os.chmod(wrapper_path, stat.S_IRWXU)
        self.env['GIT_SSH'] = wrapper_path
        self.env['GIT_COMMITTER_NAME'] = self.user
        self.env['GIT_COMMITTER_EMAIL'] = self.email

    def config_review(self, clone_dir):
        self.exe("ssh-agent bash -c 'ssh-add %s; git review -s'" %
                 self.priv_key_path, clone_dir)

    def clone(self, uri, target, config_review=True):
        if not uri.startswith('ssh://'):
            raise Exception("%s doesn't start with ssh://" % uri)
        cmd = "git clone %s %s" % (uri, target)
        self.exe(cmd, self.tempdir)
        clone = os.path.join(self.tempdir, target)
        if not os.path.isdir(clone):
            raise Exception("%s is not a directory" % clone)
        self.exe('git config --add gitreview.username %s' %
                 self.user, clone)
        if config_review:
            self.config_review(clone)
        return clone

    def fetch_meta_config(self, clone_dir):
        cmd = 'git fetch origin' \
            ' refs/meta/config:refs/remotes/origin/meta/config'
        self.exe(cmd, clone_dir)
        self.exe('git checkout meta/config', clone_dir)

    def add_commit_in_branch(self, clone_dir, branch, files=None, commit=None):
        self.exe('git checkout master', clone_dir)
        self.exe('git checkout -b %s' % branch, clone_dir)
        if not files:
            file(os.path.join(clone_dir, 'testfile'), 'w').write('data')
            files = ['testfile']
        self.git_add(clone_dir, files)
        if not commit:
            commit = "Adding testfile"
        self.exe("git commit --author '%s' -m '%s'" % (self.author, commit),
                 clone_dir)

    def add_commit_for_all_new_additions(self, clone_dir, commit=None):
        self.exe('git checkout master', clone_dir)
        if not commit:
            commit = "Add all the additions"
        self.exe('git add *', clone_dir)
        self.exe("git commit --author '%s' -m '%s'" % (self.author, commit),
                 clone_dir)

    def direct_push_branch(self, clone_dir, branch):
        self.exe('git checkout %s' % branch, clone_dir)
        self.exe('git push origin %s' % branch, clone_dir)
        self.exe('git checkout master', clone_dir)

    def review_push_branch(self, clone_dir, branch):
        self.exe('git checkout %s' % branch, clone_dir)
        self.exe('git review', clone_dir)
        self.exe('git checkout master', clone_dir)

    def git_add(self, clone_dir, files=[]):
        to_add = " ".join(files)
        self.exe('git add %s' % to_add, clone_dir)

    def add_commit_and_publish(self, clone_dir, branch,
                               commit_msg, commit_author=None,
                               fnames=None):
        self.exe('git checkout %s' % branch, clone_dir)

        if not fnames:
            # If no file names are passed, create a test file
            fname = create_random_str()
            data = 'data'
            file(os.path.join(clone_dir, fname), 'w').write(data)
            fnames = [fname]

        self.git_add(clone_dir, fnames)
        if commit_msg:
            author = '%s <%s>' % (commit_author,
                                  config.USERS[commit_author]['email']) \
                     if commit_author else self.author
            self.exe("git commit --author '%s' -m '%s'" %
                     (author, commit_msg), clone_dir)
        else:
            # If commit message is None, we need to ammend the old commit
            self.exe("git reset --soft HEAD^", clone_dir)
            self.exe("git commit -C ORIG_HEAD", clone_dir)

        self.exe('git review -v', clone_dir)


class GerritRestAPI(object):
    def __init__(self, url, user):
        self.cookie = config.USERS[user]['auth_cookie']
        self.url = url

        if not self.url.endswith('/'):
            self.url += '/'

    def make_url(self, endpoint):
        endpoint = endpoint.lstrip('/')
        return self.url + endpoint

    def get(self, endpoint, **kwargs):
        kwargs['cookies'] = dict(auth_pubtkt=self.cookie)
        resp = http.get(self.make_url(endpoint), **kwargs)
        return _decode_response(resp)

    def put(self, endpoint, **kwargs):
        kwargs['cookies'] = dict(auth_pubtkt=self.cookie)
        resp = http.put(self.make_url(endpoint), **kwargs)
        return _decode_response(resp)

    def post(self, endpoint, **kwargs):
        kwargs['cookies'] = dict(auth_pubtkt=self.cookie)
        resp = http.post(self.make_url(endpoint), **kwargs)
        return _decode_response(resp)

    def delete(self, endpoint, **kwargs):
        kwargs['cookies'] = dict(auth_pubtkt=self.cookie)
        resp = http.delete(self.make_url(endpoint), **kwargs)
        return _decode_response(resp)


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
        self.rest = GerritRestAPI(self.url, username)

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
        resp = self.rest.post('/a/accounts/self/sshkeys',
                              data=pubkey,
                              headers=headers)
        return resp['seq']

    def delPubKey(self, index):
        self.rest.delete('/a/accounts/self/sshkeys/' + str(index))

    def _submitCodeReview(self, change_id, revision_id, rate):
        reviewInput = json.dumps({"labels": {"Code-Review": int(rate)}})
        headers = {'Content-Type': 'application/json'}
        self.rest.post('/a/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput,
                       headers=headers)

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
        headers = {'Content-Type': 'application/json'}
        reviewInput = json.dumps({"labels": {"Verified": int(rate)}})
        self.rest.post('/a/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput,
                       headers=headers)

    def setPlus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '+1')

    def setMinus1Verified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '-1')

    def setNoScoreVerified(self, change_id, revision_id):
        self._submitVerified(change_id, revision_id, '0')

    def setPlus1Approved(self, change_id, revision_id):
        reviewInput = json.dumps({"labels": {"Approved": 1}})
        headers = {'Content-Type': 'application/json'}
        self.rest.post('/a/changes/%s/revisions/%s/review' %
                       (change_id, revision_id), data=reviewInput,
                       headers=headers)

    def submitPatch(self, change_id, revision_id):
        submit = json.dumps({"wait_for_merge": True})
        headers = {'Content-Type': 'application/json'}
        try:
            r = self.rest.post('/a/changes/%s/revisions/%s/submit' %
                               (change_id, revision_id), data=submit,
                               headers=headers)
            return r
        except Exception as e:
            return e.response.status_code

    def getReviewerApprovals(self, changeid, reviewer):
        resp = self.rest.get('/a/changes/%(change-id)s/reviewers/%(reviewer)s'
                             % {'change-id': changeid, 'reviewer': reviewer})
        return resp[0]['approvals']

    def getReviewers(self, changeid):
        resp = self.rest.get('/a/changes/%s/reviewers' % changeid)
        return [r['username'] for r in resp]

    def getMyChangesForProject(self, project):
        changes = self.rest.get(
            '/a/changes/?q=owner:self+project:%s' % project)
        return [c['change_id'] for c in changes]

    def getChangeDetail(self, project, branch, change_id):
        changeid = "%s %s %s" % (project, branch, change_id)
        changeid = changeid.replace(' ', '~')
        change = self.rest.get(
            '/a/changes/%s' % changeid)
        return change

    def listPlugins(self):
        plugins = self.rest.get('/a/plugins/?all')
        ret = []

        for k, v in plugins.items():
            ret.append(k)

        return plugins

    def enablePlugin(self, plugin):
        self.rest.post('/a/plugins/%s/gerrit~enable' % plugin)

    def disablePlugin(self, plugin):
        self.rest.post('/a/plugins/%s/gerrit~disable' % plugin)


class RedmineUtil:
    def __init__(self, url, username=None, apiKey=None):
        # TODO(fbo); url is useless here
        self.username = username
        self.api_key = apiKey
        if username:
            self.cookie = config.USERS[self.username]['auth_cookie']
        else:
            self.cookie = config.USERS[config.USER_1]['auth_cookie']

    def isProjectExist(self, name):
        url = "%(redmine_server)s/projects/%(prj_name)s.json" % \
              {"redmine_server": config.REDMINE_SERVER,
               "prj_name": name}
        headers = {"X-Redmine-Api-Key": self.api_key}
        resp = http.get(url, headers=headers,
                        cookies=dict(auth_pubtkt=self.cookie))
        if resp.status_code == 200:
            return True

        return False

    def isProjectExist_ex(self, name, username):
        url = "%(redmine_server)s/projects/%(prj_name)s.json" % \
              {"redmine_server": config.REDMINE_SERVER,
               "prj_name": name}
        cookie = config.USERS[username]['auth_cookie']
        resp = http.get(url,
                        cookies=dict(auth_pubtkt=cookie))
        if resp.status_code == 200:
            return True

        return False

    def issueStatus(self, issueId):
        url = "%(redmine_server)s/issues/%(issue_id)s.json" % \
              {"redmine_server": config.REDMINE_SERVER,
               "issue_id": str(issueId)}
        resp = http.get(url,
                        cookies=dict(auth_pubtkt=self.cookie))
        if resp.status_code == 200:
            return resp.json()['issue']['status']['id']

        return None

    def listIssues(self, project):
        url = "%(redmine_server)s/issues.json" % \
              {"redmine_server": config.REDMINE_SERVER}
        resp = http.get(url,
                        params={'project_id': project},
                        cookies=dict(auth_pubtkt=self.cookie))
        if resp.status_code == 200:
            return resp.json()

        return None

    def isIssueInProgress(self, issueId):
        return self.issueStatus(issueId) is 2

    def isIssueClosed(self, issueId):
        return self.issueStatus(issueId) is 5

    def createIssue(self, project, subject='None'):
        issue = {"issue":
                 {"project_id": project,
                  "subject": subject,
                  },
                 }
        data = json.dumps(issue)
        url = "%(redmine_server)s/issues.json" % \
              {"redmine_server": config.REDMINE_SERVER}
        headers = {"X-Redmine-API-Key": self.api_key,
                   "Content-type": "application/json"}
        resp = http.post(url, data=data, headers=headers,
                         cookies=dict(auth_pubtkt=self.cookie))
        ret = resp.json()
        return ret['issue']['id']

    def deleteIssue(self, issue_id):
        url = "%(redmine_server)s/%(issue_id)s.json" % \
              {"redmine_server": config.REDMINE_SERVER,
               "issue_id": issue_id}
        headers = {"X-Redmine-API-Key": self.api_key,
                   "Content-type": "application/json"}
        http.delete(url, headers=headers,
                    cookies=dict(auth_pubtkt=self.cookie))

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
        resp = http.post(url, data=data, headers=headers,
                         cookies=dict(auth_pubtkt=self.cookie))

        def current_user_id():
            url = "%(redmine_server)s/users/current.json" % \
                  {"redmine_server": config.REDMINE_SERVER}
            r = http.get(url, auth=HTTPBasicAuth(username, password),
                         cookies=dict(auth_pubtkt=self.cookie))
            if r.status_code != 200:
                return None

            return r.json()['user']['id']

        if resp.status_code != 201:
            if resp.status_code == 422:
                return current_user_id()
            return None

        ret = resp.json()
        return ret['user']['id']

    def checkUserRole(self, prj_name, user, role_name):
        url = "%(redmine_server)s/projects/%(project)s/memberships.json" % \
              {"redmine_server": config.REDMINE_SERVER,
                  "project": prj_name}
        headers = {"X-Redmine-API-Key": self.api_key}
        resp = http.get(url, headers=headers,
                        cookies=dict(auth_pubtkt=self.cookie))
        if resp.status_code != 200:
            return False

        j = resp.json()
        for m in j['memberships']:
            # This test is not strict be should be enough
            if user in m['user']['name']:
                for r in m['roles']:
                    if r['name'] == role_name:
                        return True

        return False

    def deleteUser(self, user_id):
        url = "%(redmine_server)s/%(user_id)s.xml" % \
              {"redmine_server": config.REDMINE_SERVER,
               "user_id": user_id}

        headers = {"X-Redmine-API-Key": self.api_key}
        resp = http.delete(url, headers=headers,
                           cookies=dict(auth_pubtkt=self.cookie))
        if resp.status_code == 200:
            return True

        return False


class JenkinsUtils:
    def __init__(self):
        with open('/etc/puppet/hiera/sf/jenkins.yaml') as fh:
            yconfig = yaml.load(fh)
            self.jenkins_user = 'jenkins'
            self.jenkins_password = \
                yconfig.get('jenkins').get('jenkins_password')
        self.server = config.JENKINS_SERVER

    def get(self, url):
        return requests.get(url, auth=(self.jenkins_user,
                                       self.jenkins_password))

    def post(self, url, params, data, headers):
        return requests.post(url,
                             params=params,
                             data=data,
                             headers=headers,
                             auth=(self.jenkins_user,
                                   self.jenkins_password))

    def create_job(self, name):
        url = "%s/createItem" % self.server
        headers = {'content-type': 'text/xml'}
        resp = self.post(url,
                         params={'name': name},
                         data=EMPTY_JOB_XML,
                         headers=headers)
        return resp.status_code

    def list_jobs(self):
        from xml.dom import minidom
        url = "%s/api/xml" % self.server
        resp = self.get(url)
        if resp.status_code == 200:
            jobs = []
            for job in minidom.parseString(resp.text).\
                    getElementsByTagName('job'):
                jobs.append(job.firstChild.childNodes[0].data)
            return jobs
        return None

    def get_last_build_number(self, job_name, type):
        url = "%(server)s/job/%(job_name)s/%(type)s/buildNumber" \
              % {'server': self.server, 'job_name': job_name, 'type': type}
        try:
            resp = self.get(url)
            return int(resp.text)
        except:
            return 0

    def wait_till_job_completes(self, job_name, last, type):
        retries = 0
        while True:
            cur = self.get_last_build_number(job_name, type)
            if cur > last:
                break
            elif retries > 30:
                break
            else:
                time.sleep(1)
                retries += 1
