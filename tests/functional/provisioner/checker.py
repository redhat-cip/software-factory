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
import shlex
import requests
import sys
import yaml

pwd = os.path.dirname(os.path.abspath(__file__))  # flake8: noqa
sys.path.append(os.path.dirname(pwd))             # flake8: noqa
import config

from utils import get_cookie
from pysflib.sfgerrit import GerritUtils
from utils import GerritGitUtils
from utils import JenkinsUtils
from utils import is_present
from utils import ssh_run_cmd

from pysflib.sfstoryboard import SFStoryboard


class SFchecker:
    """ This checker is only intended for testin
    SF backup/restore and update. It checks that the user
    data defined in resourses.yaml are present on the SF.

    Those data must have been provisioned by SFProvisioner.
    """
    def __init__(self):
        with open("%s/resources.yaml" % pwd, 'r') as rsc:
            self.resources = yaml.load(rsc)
        config.USERS[config.ADMIN_USER]['auth_cookie'] = get_cookie(
            config.ADMIN_USER, config.USERS[config.ADMIN_USER]['password'])
        self.gu = GerritUtils(
            'http://%s/' % config.GATEWAY_HOST,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.ggu = GerritGitUtils(config.ADMIN_USER,
                                  config.ADMIN_PRIV_KEY_PATH,
                                  config.USERS[config.ADMIN_USER]['email'])
        self.ju = JenkinsUtils()
        self.stb_client = SFStoryboard(
            config.GATEWAY_URL + "/storyboard_api",
            config.USERS[config.ADMIN_USER]['auth_cookie'])

    def check_project(self, name):
        print " Check project %s exists ..." % name,
        if not self.gu.project_exists(name):
            print "FAIL"
            exit(1)
        if is_present('storyboard'):
            if name not in [p.name for p in self.stb_client.projects.get_all()]:
                print "FAIL"
                exit(1)
        print "OK"

    def check_files_in_project(self, name, files):
        print " Check files(%s) exists in project ..." % ",".join(files),
        # TODO(fbo); use gateway host instead of gerrit host
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, name)
        clone_dir = self.ggu.clone(url, name, config_review=False)
        for f in files:
            if not os.path.isfile(os.path.join(clone_dir, f)):
                print "FAIL"
                exit(1)

    def check_issues_on_project(self, name, issues):
        print (" Check that at least %s issues exists "
               "for that project ..." % len(issues))
        p = [p for p in self.stb_client.projects.get_all()
             if p.name == name][0]
        pt = [t for t in self.stb_client.tasks.get_all() if
              t.project_id == p.id]
        if len(pt) != len(issues):
            print "FAIL: expected %s, project has %s" % (
                len(issues), len(pt))
            exit(1)
        print "OK"

    def check_jenkins_jobs(self, name, jobnames):
        print " Check that jenkins jobs(%s) exists ..." % ",".join(jobnames)
        for jobname in jobnames:
            if not '%s_%s' % (name, jobname) in self.ju.list_jobs():
                print "FAIL"
                exit(1)
        print "OK"

    def check_reviews_on_project(self, name, issues):
        reviews = [i for i in issues if i['review']]
        print " Check that at least %s reviews exists for that project ..." %\
            len(reviews),
        pending_reviews = self.ggu.list_open_reviews(name, config.GATEWAY_HOST)
        if not len(pending_reviews) >= len(reviews):
            print "FAIL"
            exit(1)
        print "OK"

    def check_pads(self, amount):
        pass

    def check_pasties(self, amount):
        pass

    def command(self, cmd):
        return ssh_run_cmd(os.path.expanduser("~/.ssh/id_rsa"),
                           "root",
                           config.GATEWAY_HOST, shlex.split(cmd))

    def compute_checksum(self, f):
        out = self.command("md5sum %s" % f)[0]
        if out:
            return out.split()[0]

    def read_file(self, f):
        return self.command("cat %s" % f)[0]

    def simple_login(self, user, password):
        """log as user"""
        return get_cookie(user, password)

    def check_users_list(self):
        print "Check that users are listable ...",
        users = [u['name'] for u in self.resources['users']]
        c = {'auth_pubtkt': config.USERS[config.ADMIN_USER]['auth_cookie']}
        url = 'http://%s/manage/services_users/' % config.GATEWAY_HOST
        registered = requests.get(url,
                                  cookies=c).json()
        # usernames are in first position
        r_users = [u['username'] for u in registered]
        if not set(users).issubset(set(r_users)):
            print "FAIL: expected %s, got %s" % (users, r_users)
            exit(1)
        print "OK"

    def check_checksums(self):
        print "Check that expected file are there"
        checksum_list = yaml.load(file('pc_checksums.yaml'))
        mismatch = False
        for f, checksum in checksum_list.items():
            if f.startswith("content_"):
                continue
            c = self.compute_checksum(f)
            if c == checksum:
                print "Expected checksum (%s) for %s is OK." % (
                    checksum, f)
            else:
                print "Expected checksum (%s) for %s is WRONG (%s)." % (
                    checksum, f, c)
                print "New file is:"
                print "    %s" % self.read_file(f).replace("\n", "\n    ")
                print "Old file was:"
                print "    %s" % checksum_list['content_' + f].replace("\n",
                    "\n    ")
                mismatch = True
        if "checksum_warn_only" not in sys.argv and mismatch:
            sys.exit(1)

    def checker(self):
        self.check_checksums()
        self.check_users_list()
        for project in self.resources['projects']:
            print "Check user datas for %s" % project['name']
            self.check_project(project['name'])
            self.check_files_in_project(project['name'],
                                        [f['name'] for f in project['files']])
            if is_present('storyboard'):
                self.check_issues_on_project(project['name'],
                                             project['issues'])
            self.check_reviews_on_project(project['name'], project['issues'])
            self.check_jenkins_jobs(project['name'],
                                    [j['name'] for j in project['jobnames']])
        self.check_pads(2)
        self.check_pasties(2)
        for user in self.resources['local_users']:
            print "Check user %s can log in ..." % user['username'],
            if self.simple_login(user['username'],
                                 user['password']):
                print "OK"
            else:
                print "FAIL"
                exit(1)

c = SFchecker()
c.checker()
