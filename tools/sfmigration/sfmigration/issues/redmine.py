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


from sfmigration.common import base
from sfmigration.common import utils


logger = utils.logger


class RedmineImporter(base.BaseRedmine, base.BaseIssueImporter):
    def __init__(self, username=None, password=None,
                 apikey=None, id=None, url=None, name=None):
        super(RedmineImporter, self).__init__(username, password,
                                              apikey, id, url, name)
        if not self.id:
            projects = self.redmine.project.all()
            id_candidates = [p.id for p in projects if p.name == self.name]
            try:
                self.id = id_candidates[0]
                logger.debug("Found project #%i" % self.id)
            except IndexError:
                logger.error("Project %s not found" % self.name)
                raise
        if not self.name:
            self.name = self.redmine.project.get(self.id)

    def fetch_issues(self):
        for issue in self.redmine.issue.filter(project_id=self.id,
                                               status_id='*'):
            logger.debug('Fetching issue %s: %s' % (issue.id, issue.subject))
            issue_data = {'source_id': issue.id,
                          'priority_id': 1  # set default priority to be safe
                          }
            if getattr(issue, 'subject', None):
                issue_data['subject'] = issue.subject
            if getattr(issue, 'description', None):
                issue_data['description'] = issue.description
            if getattr(issue, 'tracker', None):
                issue_data['tracker_id'] = issue.tracker.id
                issue_data['tracker_name'] = issue.tracker.name
            if getattr(issue, 'status', None):
                issue_data['status_id'] = issue.status.id
                issue_data['status_name'] = issue.status.name
            if getattr(issue, 'priority', None):
                issue_data['priority_id'] = issue.priority.id
                issue_data['priority_name'] = issue.priority.name
            if getattr(issue, 'done_ratio', None):
                issue_data['done_ratio'] = issue.done_ratio
            if getattr(issue, 'story_points', None):
                issue_data['story_points'] = issue.story_points
            if getattr(issue, 'fixed_version', None):
                issue_data['fixed_version_id'] = issue.fixed_version.id
                issue_data['version_name'] = issue.fixed_version.name
            if getattr(issue, 'assigned_to', None):
                issue_data['assigned_to_id'] = issue.assigned_to.id
                login = self.redmine.user.get(issue.assigned_to.id).login
                issue_data['assigned_to_login'] = login
            yield issue_data

    def fetch_versions(self):
        for version in self.redmine.version.filter(project_id=self.id):
            logger.debug("Fetching version %s: %s" % (version.id,
                                                      version.name))
            version_data = {}
            version_data['source_id'] = version.id
            version_data['name'] = version.name
            if getattr(version, 'status', None):
                version_data['status'] = version.status
            yield version_data
