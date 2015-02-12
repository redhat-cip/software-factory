#!/usr/bin/python
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


from redmine.managers import ResourceBadMethodError

from pysflib import sfauth
from pysflib import sfredmine
from sfmigration.common import base
from sfmigration.common import utils


logger = utils.logger


def redmine_valid_api_method(resource):
    def decorator(f):
        def decorated(*args, **kwargs):
            try:
                f(*args, **kwargs)
            except NotImplementedError:
                log_msg = "Importing %s is not supported, skipping." % resource
                logger.warning(log_msg)
            except ResourceBadMethodError:
                log_msg = "Creating %s not supported by redmine API, skipping."
                logger.warning(log_msg % resource)
        return decorated
    return decorator


class SFRedmineMigrator(base.BaseRedmine):
    def __init__(self, username=None, password=None,
                 apikey=None, id=None, url=None, name=None,
                 sf_domain=None, versions_to_skip=None, issues_to_skip=None,
                 mapper=None, use_ssl=True, verify_ssl=False):
        self.sf_domain = sf_domain
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        if self.use_ssl and str(url).startswith('http://'):
            logger.debug("migration url not using SSL, disabling SSL")
            self.use_ssl = False
            self.verify_ssl = False
        super(SFRedmineMigrator, self).__init__(username, password,
                                                apikey, id, url, name)
        if not self.id:
            projects = self.redmine.project.all()
            logger.debug("Fetched %i projects" % len(projects))
            id_candidates = [p.id for p in projects if p.name == self.name]
            try:
                self.id = id_candidates[0]
                logger.debug("Found project #%i" % self.id)
            except IndexError:
                log_msg = "Project %s not found on %s" % (self.name, self.url)
                log_msg += ", creating it"
                logger.warning(log_msg)
                p_identifier = "-".join(self.name.lower().split(' '))
                project = self.redmine.project.create(name=self.name,
                                                      identifier=p_identifier)
                self.id = project.id
        if not self.name:
            self.name = self.redmine.project.get(self.id)
        self.versions_to_update = {}
        self.versions_to_skip = versions_to_skip
        if not self.versions_to_skip:
            self.versions_to_skip = []
        self.issues_to_skip = issues_to_skip
        if not self.issues_to_skip:
            self.issues_to_skip = []
        if mapper:
            self.mapper = mapper
        else:
            self.mapper = utils.BaseMapper()

    def _create_connector(self):
        c = sfauth.get_cookie(self.sf_domain, self.username, self.password,
                              use_ssl=self.use_ssl, verify=self.verify_ssl)
        self.redmine = sfredmine.SFRedmine(self.url, auth_cookie=c,
                                           requests={'verify': False})

    def migrate(self, importer):
        self.migrate_trackers(importer)
        self.migrate_wiki(importer)
        self.migrate_issue_statuses(importer)
        self.migrate_versions(importer)
        self.migrate_issues(importer)
        self.cleanup(importer)

    @redmine_valid_api_method("trackers")
    def migrate_trackers(self, importer):
        for tracker in importer.fetch_trackers():
            self.redmine.tracker.create(**tracker)

    @redmine_valid_api_method("wiki pages")
    def migrate_wiki(self, importer):
        for article in importer.fetch_wiki():
            self.redmine.wiki_page.create(**article)

    @redmine_valid_api_method("issue statuses")
    def migrate_issue_statuses(self, importer):
        for status in importer.fetch_issue_statuses():
            self.redmine.issue_status.create(**status)

    @redmine_valid_api_method("versions")
    def migrate_versions(self, importer):
        for version in importer.fetch_versions():
            if str(version['source_id']) not in self.versions_to_skip:
                del version['source_id']
                logger.debug("Migrating version '%s' ..." % version['name'])
                version['project_id'] = self.id
                real_version = None
                if version['status'] != 'open':
                    # open the version so we can add issues to it
                    real_version = version['status']
                    version['status'] = 'open'
                new_version = self.redmine.version.create(**version)
                if real_version:
                    self.versions_to_update[new_version.id] = real_version
            else:
                logger.debug("Skipping version #%s" % version['source_id'])

    def migrate_issues(self, importer):
        for issue in importer.fetch_issues():
            if str(issue['source_id']) in self.issues_to_skip:
                logger.debug("Skipping issue #%s" % issue['source_id'])
            else:
                log_msg = "Migrating issue #%s: %s ..." % (issue['source_id'],
                                                           issue['subject'])
                logger.debug(log_msg)
                issue['project_id'] = self.id
                # check tracker
                if 'tracker_name' in issue:
                    mapped_tracker = self.mapper.map(issue['tracker_name'])
                    possible_trackers = [t.id
                                         for t in self.redmine.tracker.all()
                                         if t.name == mapped_tracker]
                    try:
                        issue['tracker_id'] = possible_trackers[0]
                    except IndexError:
                        log_msg = "Tracker %s not found, leaving empty"
                        logger.debug(log_msg % mapped_tracker)
                        del issue['tracker_id']
                # check issue status
                if 'status_name' in issue:
                    mapped_status = self.mapper.map(issue['status_name'])
                    possible_status = [t.id
                                       for t in self.redmine.issue_status.all()
                                       if t.name == mapped_status]
                    try:
                        issue['status_id'] = possible_status[0]
                    except IndexError:
                        log_msg = "Status %s not found, leaving empty"
                        logger.debug(log_msg % mapped_status)
                        if 'status_id' in issue:
                            del issue['status_id']
                # check version
                if 'version_name' in issue:
                    mapped_version = self.mapper.map(issue['version_name'])
                    possible_versions = [t.id for t in
                                         (self.redmine.version
                                          .filter(project_id=self.id))
                                         if t.name == mapped_version]
                    try:
                        issue['fixed_version_id'] = possible_versions[0]
                    except IndexError:
                        log_msg = "Version %s not found, leaving empty"
                        logger.debug(log_msg % mapped_version)
                        if 'fixed_version_id' in issue:
                            del issue['fixed_version_id']
                # check user
                if 'assigned_to_login' in issue:
                    mapped_user = self.mapper.map(issue['assigned_to_login'])
                    possible_users = [t.id for t in
                                      (self.redmine.user
                                       .filter(name=mapped_user))
                                      if t.login == mapped_user]
                    try:
                        log_msg = "User %s mapped to #%s"
                        logger.debug(log_msg % (issue['assigned_to_login'],
                                                possible_users[0]))
                        issue['assigned_to_id'] = possible_users[0]
                    except IndexError:
                        log_msg = "User %s not found, leaving empty"
                        logger.debug(log_msg % mapped_user)
                        if 'assigned_to_id' in issue:
                            del issue['assigned_to_id']
                # check priority
                if 'priority_name' in issue:
                    mapped_priority = self.mapper.map(issue['priority_name'])
                    possible_priority = [t.id for t in
                                         (self.redmine.enumeration
                                          .filter(resource='issue_priorities'))
                                         if t.name == mapped_priority]
                    try:
                        issue['priority_id'] = possible_priority[0]
                    except IndexError:
                        log_msg = ("Priority %s not found, "
                                   "setting default priority 1")
                        logger.debug(log_msg % mapped_version)
                        issue['priority_id'] = 1
                # clean unneeded values at this point
                for unneeded in ('tracker_name', 'status_name',
                                 'fixed_version_name', 'priority_name',
                                 'assigned_to_login', 'source_id'):
                    try:
                        del issue[unneeded]
                    except KeyError:
                        pass
                # create the issue finally!
                self.redmine.issue.create(**issue)

    def cleanup(self, *args, **kwargs):
        for version, status in self.versions_to_update.items():
            logger.debug("Re-setting correct status for version #%i" % version)
            self.redmine.version.update(version, status=status)
