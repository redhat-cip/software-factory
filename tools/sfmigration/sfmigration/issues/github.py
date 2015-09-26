#!/bin/env python
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import github3

from sfmigration.common import base
from sfmigration.common import utils


logger = utils.logger


class GithubImporter(base.BaseIssueImporter):

    def __init__(self, repository, repo_owner,
                 username=None, password=None):
        self.username = username
        self.password = password
        self.repository = repository
        self.repo_owner = repo_owner
        if not self.username and not self.password:
            github = github3.GitHub()
        else:
            github = github3.login(username,
                                   password=password)
        self.repo = github.repository(self.repo_owner,
                                      self.repository)

    def fetch_issues(self):
        try:
            iterator = self.repo.iter_issues
        except AttributeError:
            iterator = self.repo.issues
        for issue in iterator(state='all'):
            # is this a pull request ?
            if getattr(issue, 'pull_request', None):
                msg = 'Skipping pull request %s: %s' % (issue.id, issue.title)
                logger.debug(msg)
                continue
            msg = 'Skipping pull request %s: %s' % (issue.id, issue.title)
            logger.debug(msg)
            issue_data = {'source_id': issue.id,
                          'priority_id': 1  # set default priority to be safe
                          }
            if getattr(issue, 'title', None):
                issue_data['subject'] = issue.title
            if getattr(issue, 'body', None):
                try:
                    issue_data['description'] = issue.body_text
                except:
                    issue_data['description'] = issue.body
            if getattr(issue, 'tracker', None):
                # not available on github
                pass
            if getattr(issue, 'state', None):
                # the default redmine statuses start with a capital letter
                issue_data['status_name'] = issue.state.title()
            if getattr(issue, 'priority', None):
                # not available on github
                pass
            if getattr(issue, 'done_ratio', None):
                # not available on github
                pass
            if getattr(issue, 'story_points', None):
                # not available on github
                pass
            if getattr(issue, 'milestone', None):
                issue_data['fixed_version_id'] = issue.milestone.number
                issue_data['version_name'] = issue.milestone.title
            if getattr(issue, 'assignee', None):
                issue_data['assigned_to_id'] = issue.assignee.id
                login = issue.assignee.login
                issue_data['assigned_to_login'] = login
            yield issue_data

    def fetch_versions(self):
        try:
            iterator = self.repo.iter_milestones
        except AttributeError:
            iterator = self.repo.milestones
        for version in iterator():
            logger.debug("Fetching version %s: %s" % (version.number,
                                                      version.title))
            version_data = {}
            version_data['source_id'] = version.number
            version_data['name'] = version.title
            if getattr(version, 'state', None):
                version_data['status'] = version.state
            yield version_data
