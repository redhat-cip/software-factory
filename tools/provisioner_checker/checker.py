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
import sys

lib_path = os.path.join(os.environ["SF_ROOT"], "tests/functional")
sys.path.append(lib_path)

import yaml
import config

from utils import get_cookie
from pysflib.sfredmine import RedmineUtils
from pysflib.sfgerrit import GerritUtils
from utils import GerritGitUtils
from utils import JenkinsUtils


class SFchecker:
    """ This checker is only intended for testin
    SF backup/restore and update. It checks that the user
    data defined in resourses.yaml are present on the SF.

    Those data must have been provisioned by SFProvisioner.
    """
    def __init__(self):
        with open('resources.yaml', 'r') as rsc:
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
        self.rm = RedmineUtils(
            config.REDMINE_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])

    def check_project(self, name):
        print " Check project %s exists ..." % name
        assert self.gu.project_exists(name)
        assert self.rm.project_exists(name)

    def check_files_in_project(self, name, files):
        print " Check files(%s) exists in project ..." % ",".join(files)
        # TODO(fbo); use gateway host instead of gerrit host
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, name)
        clone_dir = self.ggu.clone(url, name, config_review=False)
        for f in files:
            assert os.path.isfile(os.path.join(clone_dir, f))

    def check_issues_on_project(self, name, issues):
        print " Check that at least %s issues exists for that project ..." %\
            len(issues)
        current_issues = self.rm.get_issues_by_project(name)
        if len(current_issues) < len(issues):
            msg = "expected %s, project has %s" % (len(issues),
                                                   len(current_issues))
            raise AssertionError(msg)

    def check_jenkins_jobs(self, name, jobnames):
        print " Check that jenkins jobs(%s) exists ..." % ",".join(jobnames)
        for jobname in jobnames:
            assert '%s_%s' % (name, jobname) in self.ju.list_jobs()

    def check_reviews_on_project(self, name, issues):
        reviews = [i for i in issues if i['review']]
        print " Check that at least %s reviews exists for that project ..." %\
            len(reviews)
        pending_reviews = self.ggu.list_open_reviews(name, config.GATEWAY_HOST)
        assert len(pending_reviews) >= len(reviews)

    def check_pads(self, amount):
        pass

    def check_pasties(self, amount):
        pass

    def checker(self):
        for project in self.resources['projects']:
            print "Check user datas for %s" % project['name']
            self.check_project(project['name'])
            self.check_files_in_project(project['name'],
                                        [f['name'] for f in project['files']])
            self.check_issues_on_project(project['name'], project['issues'])
            self.check_reviews_on_project(project['name'], project['issues'])
            self.check_jenkins_jobs(project['name'],
                                    [j['name'] for j in project['jobnames']])
        self.check_pads(2)
        self.check_pasties(2)


c = SFchecker()
c.checker()
