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

import json
import os
import unittest
import subprocess
import shlex
import shutil
import stat
import tempfile
import string
import random
import config
import requests
import time
import yaml

import logging
import pkg_resources

from pysflib.sfredmine import RedmineUtils

from subprocess import Popen, PIPE


logging.getLogger("requests").setLevel(logging.WARNING)
logging.captureWarnings(True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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


# for easier imports
skipIf = unittest.skipIf
skip = unittest.skip


# test decorators and utilities related to running services
def _get_services():
    cookie = get_cookie(config.ADMIN_USER,
                        config.USERS[config.ADMIN_USER]['password'])
    about = requests.get(config.GATEWAY_URL + '/manage/about/',
                         headers={'Accept': 'application/json'},
                         cookies={'auth_pubtkt': cookie})
    if about.status_code > 399:
        return []
    try:
        return about.json()['service']['services']
    except ValueError:
        raise Exception("Cannot get services from %s" % (config.GATEWAY_URL +
                                                         '/manage/about/'))


def is_present(service):
    return service in _get_services()


def has_issue_tracker():
    return set(config.ISSUE_TRACKERS) & set(_get_services())


def skipIfServiceMissing(service):
    services = _get_services()
    if not services:
        logger.warning('Introspection endpoint not available, you are '
                       'probably testing a old version of SF, skipping test')
        return skip
    return skipIf(service not in services,
                  'This instance of SF is not running %s' % service)


def skipIfServicePresent(service):
    services = _get_services()
    if not services:
        logger.warning('Introspection endpoint not available, you are '
                       'probably testing a old version of SF, skipping test')
        return skip
    return skipIf(service in services,
                  'This instance of SF is running %s' % service)


def skipIfIssueTrackerMissing():
    services = _get_services()
    if not services:
        logger.warning('Introspection endpoint not available, you are '
                       'probably testing a old version of SF, skipping test')
        return skip
    return skipIf(not set(config.ISSUE_TRACKERS) & set(services),
                  'This instance of SF is not running any issue tracker')


def skipIfIssueTrackerPresent():
    services = _get_services()
    if not services:
        logger.warning('Introspection endpoint not available, you are '
                       'probably testing a old version of SF, skipping test')
        return skip
    tracker = list(set(config.ISSUE_TRACKERS) & set(services))
    if tracker:
        return skipIf(
            'This instance of SF is running %s' % ', '.join(tracker))


def get_issue_tracker_utils(*args, **kwargs):
    """Returns the correct utility instance depending on the issue tracker
    being deployed with Software Factory"""
    services = _get_services()
    if not services:
        logger.warning('Introspection endpoint not available, you are '
                       'probably testing a old version of SF')
        return RedmineUtils(config.GATEWAY_URL + "/redmine/",
                            *args, **kwargs)
    if 'SFRedmine' in services:
        return RedmineUtils(config.GATEWAY_URL + "/redmine/",
                            *args, **kwargs)
    else:
        from pysflib.interfaces.issuetracker import IssueTrackerUtils
        return IssueTrackerUtils(config.GATEWAY_URL,
                                 *args, **kwargs)


def get_module_version(module):
    m = module
    if not isinstance(m, basestring):
        m = module.__name__
    try:
        return pkg_resources.get_distribution(m).version
    except pkg_resources.DistributionNotFound:
        # module not available, return dummy version
        return "0"


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
    url = "%(auth_url)s/auth/login" % {'auth_url': config.GATEWAY_URL}
    resp = requests.post(url, params={'username': username,
                                      'password': password,
                                      'back': '/'},
                         allow_redirects=False)
    return resp.cookies.get('auth_pubtkt', '')


def ssh_run_cmd(sshkey_priv_path, user, host, subcmd):
    host = '%s@%s' % (user, host)
    sshcmd = ['ssh', '-o', 'LogLevel=ERROR',
              '-o', 'StrictHostKeyChecking=no',
              '-o', 'UserKnownHostsFile=/dev/null', '-i',
              sshkey_priv_path, host]
    cmd = sshcmd + subcmd

    p = Popen(cmd, stdout=PIPE)
    return p.communicate()


class Base(unittest.TestCase):
    pass


class Tool:
    def __init__(self):
        self.env = os.environ.copy()

    def exe(self, cmd, cwd=None):
        logger.debug('Starting Process "%s"' % cmd)
        cmd = shlex.split(cmd)
        ocwd = os.getcwd()
        output = ''
        if cwd:
            os.chdir(cwd)
        try:
            output = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, env=self.env)
            if output:
                logger.debug('Process Output [%s]' % output.strip())
        except subprocess.CalledProcessError as err:
            if err.output:
                logger.exception("Process Exception: %s: [%s]" %
                                 (err, err.output))
            else:
                logger.exception(err)
        finally:
            os.chdir(ocwd)
        return output


class ManageSfUtils(Tool):
    def __init__(self, url):
        Tool.__init__(self)
        self.base_cmd = "sfmanager --url %s --auth-server-url " \
            "%s --auth %%s:%%s " % (url, config.GATEWAY_URL)

    def createProject(self, name, user, options=None, cookie=None):
        passwd = config.USERS[user]['password']
        base_cmd = self.base_cmd % (user, passwd)
        if cookie:
            base_cmd = base_cmd + " --cookie %s " % (cookie)

        cmd = base_cmd + " project create --name %s " % name
        if options:
            for k, v in options.items():
                cmd = cmd + " --" + k + " " + v

        self.exe(cmd)

    def deleteProject(self, name, user):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd + " project delete --name %s"
        cmd = cmd % (user, passwd, name)
        self.exe(cmd)

    def addUsertoProjectGroups(self, auth_user, project, new_user, groups):
        passwd = config.USERS[auth_user]['password']
        umail = config.USERS[new_user]['email']
        cmd = self.base_cmd % (auth_user, passwd)
        cmd = cmd + " membership add --project %s " % project
        cmd = cmd + " --user %s --groups %s" % (umail, groups)
        self.exe(cmd)

    def deleteUserFromProjectGroups(self, auth_user,
                                    project, user, group=None):
        passwd = config.USERS[auth_user]['password']
        umail = config.USERS[user]['email']
        cmd = self.base_cmd % (auth_user, passwd) + "membership remove "
        cmd = cmd + " --project %s --user %s " % (project, umail)
        if group:
            cmd = cmd + " --group %s " % group
        self.exe(cmd)

    def list_active_members(self, user):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + " sf_user list"
        output = self.exe(cmd)
        # TODO Dangerous ! but will have to do for now
        return eval(output)

    def register_user(self, auth_user, username, email):
        passwd = config.USERS[auth_user]['password']
        cmd = self.base_cmd % (auth_user, passwd) + " sf_user create "
        cmd += "--username %s --email %s --fullname %s" % (username, email,
                                                           username)
        output = self.exe(cmd)
        return output

    def deregister_user(self, auth_user, username=None, email=None):
        passwd = config.USERS[auth_user]['password']
        cmd = self.base_cmd % (auth_user, passwd) + "sf_user delete"
        if username:
            cmd += " --username %s" % username
        else:
            cmd += " --email %s" % email
        output = self.exe(cmd)
        return output

    def create_gerrit_api_password(self, user):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + \
            "gerrit_api_htpasswd generate_password"
        output = self.exe(cmd)
        return output

    def delete_gerrit_api_password(self, user):
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + \
            "gerrit_api_htpasswd delete_password"
        output = self.exe(cmd)
        return output

    def create_user(self, user, password, email):
        subcmd = (" user create --username=%s "
                  "--password=%s --email=%s "
                  "--fullname=%s" % (user, password, email, user))
        auth_user = config.ADMIN_USER
        auth_password = config.USERS[config.ADMIN_USER]['password']
        cmd = self.base_cmd % (auth_user, auth_password) + subcmd
        output = self.exe(cmd)
        return output

    def create_init_tests(self, project, user):
        subcmd = " tests init --project=%s" % project
        passwd = config.USERS[user]['password']
        cmd = self.base_cmd % (user, passwd) + subcmd
        output = self.exe(cmd)
        return output

    def update_project_page(self, user, project, url):
        passwd = config.USERS[user]['password']
        subcmd = " pages update --name %s --dest %s" % (project, url)
        cmd = self.base_cmd % (user, passwd) + subcmd
        output = self.exe(cmd)
        return output

    def get_project_page(self, user, project):
        passwd = config.USERS[user]['password']
        subcmd = " pages get --name %s" % project
        cmd = self.base_cmd % (user, passwd) + subcmd
        output = self.exe(cmd)
        return output

    def delete_project_page(self, user, project):
        passwd = config.USERS[user]['password']
        subcmd = " pages delete --name %s" % project
        cmd = self.base_cmd % (user, passwd) + subcmd
        output = self.exe(cmd)
        return output


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
        # We also ensure the domain configured in the .gitreview is
        # according the one from sfconfig.yaml. It is usefull in
        # the case we try a domain reconfigure as the .git review of the
        # config repo has been initialized with another domain.
        self.exe("sed -i 's/^host=.*/host=%s/' .gitreview" %
                 config.GATEWAY_HOST, clone_dir)
        self.exe("ssh-agent bash -c 'ssh-add %s; git review -s'" %
                 self.priv_key_path, clone_dir)
        self.exe("git reset --hard", clone_dir)

    def list_open_reviews(self, project, uri, port=29418):
        cmd = "ssh -o StrictHostKeyChecking=no -i %s"
        cmd += " -p %s %s@%s gerrit "
        cmd += "query project:%s status:open --format=JSON"
        reviews = self.exe(cmd % (os.path.abspath(self.priv_key_path),
                                  str(port),
                                  self.user,
                                  uri,
                                  project))

        # encapsulate the JSON answers so that it appears as an array
        array_json = "[" + ',\n'.join(reviews.split('\n')[:-1]) + "]"
        j = json.loads(array_json)
        # last response element is only statistics, discard it
        return j[:-1]

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
        if branch != 'master':
            self.exe('git checkout -b %s' % branch, clone_dir)
        if not files:
            file(os.path.join(clone_dir, 'testfile'), 'w').write('data')
            files = ['testfile']
        self.git_add(clone_dir, files)
        if not commit:
            commit = "Adding some files"
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

    def get_branches(self, clone_dir, include_remotes=False):
        cmd = 'git branch'
        if include_remotes:
            cmd += ' --remote'
        out = self.exe(cmd, clone_dir)
        return out.split()


class JenkinsUtils:
    def __init__(self):
        with open('%s/hiera/sfcreds.yaml' % config.SF_BOOTSTRAP_DATA) as fh:
            yconfig = yaml.load(fh)
            self.jenkins_user = 'jenkins'
            self.jenkins_password = \
                yconfig.get('creds_jenkins_user_password')
        self.jenkins_url = config.GATEWAY_URL + "/jenkins/"
        self.cookies = {'auth_pubtkt': get_cookie(config.USER_1,
                                                  config.USER_1_PASSWORD)}

    def get(self, url):
        return requests.get(url,
                            auth=(self.jenkins_user, self.jenkins_password),
                            cookies=self.cookies)

    def post(self, url, params, data, headers):
        return requests.post(url,
                             params=params,
                             data=data,
                             headers=headers,
                             auth=(self.jenkins_user,
                                   self.jenkins_password),
                             cookies=self.cookies)

    def create_job(self, name):
        url = "%s/createItem" % self.jenkins_url
        headers = {'content-type': 'text/xml'}
        resp = self.post(url,
                         params={'name': name},
                         data=EMPTY_JOB_XML,
                         headers=headers)
        return resp.status_code

    def list_jobs(self):
        from xml.dom import minidom
        url = "%s/api/xml" % self.jenkins_url
        resp = self.get(url)
        if resp.status_code == 200:
            jobs = []
            for job in minidom.parseString(resp.text).\
                    getElementsByTagName('job'):
                jobs.append(job.firstChild.childNodes[0].data)
            return jobs
        return None

    def get_last_build_number(self, job_name, type):
        url = "%(server)sjob/%(job_name)s/%(type)s/buildNumber" % {
            'server': self.jenkins_url, 'job_name': job_name, 'type': type}
        try:
            resp = self.get(url)
            return int(resp.text)
        except:
            return 0

    def wait_till_job_completes(self, job_name, last, type, max_retries=120):
        retries = 0
        while True:
            cur = self.get_last_build_number(job_name, type)
            if cur > last:
                break
            elif retries > max_retries:
                break
            else:
                time.sleep(1)
                retries += 1
