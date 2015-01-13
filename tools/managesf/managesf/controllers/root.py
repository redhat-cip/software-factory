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
import time

from pecan import expose
from pecan import abort
from pecan.rest import RestController
from pecan import request, response
from managesf.controllers import gerrit, redminec, backup
import logging
import os.path


logger = logging.getLogger(__name__)

LOGERRORMSG = "Unable to process client request, failed with "\
              "unhandled error: %s"
CLIENTERRORMSG = "Unable to process your request, failed with "\
                 "unhandled error (server side): %s"

# TODO: add detail (detail arg or abort function) for all abort calls.


def report_unhandled_error(exp):
    logger.exception(LOGERRORMSG % str(exp))
    response.status = 500
    return CLIENTERRORMSG % str(exp)


class ReplicationController(RestController):
    # 'add','rename-section'
    @expose()
    def put(self, section=None, setting=None):
        if not section or ('value' not in request.json):
            abort(400)
        value = request.json['value']
        try:
            gerrit.replication_apply_config(section, setting, value)
        except Exception, e:
            return report_unhandled_error(e)

    # 'unset', 'replace-all', 'remove-section'
    @expose()
    def delete(self, section=None, setting=None):
        if not section:
            abort(400)
        try:
            gerrit.replication_apply_config(section, setting)
        except Exception, e:
            return report_unhandled_error(e)

    # 'get-all', 'list'
    @expose()
    def get(self, section=None, setting=None):
        if not section:
            abort(400)
        try:
            config = gerrit.replication_get_config(section, setting)
            response.status = 200
            return config
        except Exception, e:
            return report_unhandled_error(e)

    @expose()
    def post(self):
        # A json with wait, url, project can be passed
        inp = request.json if request.content_length else {}
        try:
            gerrit.replication_trigger(inp)
        except Exception, e:
            return report_unhandled_error(e)


class BackupController(RestController):
    @expose()
    def get(self):
        # TODO: avoid using directly /tmp
        filepath = '/tmp/sf_backup.tar.gz'
        try:
            backup.backup_get()
        except Exception, e:
            return report_unhandled_error(e)
        if not os.path.isfile(filepath):
            abort(404)
        response.body_file = open(filepath, 'rb')
        return response

    @expose()
    def post(self):
        try:
            backup.backup_start()
        except Exception, e:
            return report_unhandled_error(e)


class RestoreController(RestController):
    @expose()
    def post(self):
        # TODO: avoid using directly /tmp
        filepath = '/tmp/sf_backup.tar.gz'
        with open(filepath, 'wb+') as f:
            f.write(request.POST['file'].file.read())
        try:
            backup.backup_restore()
        except Exception, e:
            return report_unhandled_error(e)


class MembershipController(RestController):
    # Get method is mandatory for routing
    @expose()
    def get(self):
        abort(501)

    @expose()
    def put(self, project=None, user=None):
        if not project or not user:
            abort(400)
        inp = request.json if request.content_length else {}
        if 'groups' not in inp:
            abort(400)
        try:
            # Add/update user for the project groups
            gerrit.add_user_to_projectgroups(project, user, inp['groups'])
            redminec.add_user_to_projectgroups(project, user, inp['groups'])
            response.status = 201
            return "User %s has been added in group(s): %s for project %s" % \
                (user, ", ".join(inp['groups']), project)
        except Exception, e:
            return report_unhandled_error(e)

    @expose()
    def delete(self, project=None, user=None, group=None):
        if not project or not user:
            abort(400)
        try:
            # delete user from all project groups
            gerrit.delete_user_from_projectgroups(project, user, group)
            redminec.delete_user_from_projectgroups(project, user, group)
            response.status = 200
            if group:
                return "User %s has been deleted from group %s for project %s." % \
                    (user, group, project)
            else:
                return "User %s has been deleted from all groups for project %s." % \
                    (user, project)
        except Exception, e:
            return report_unhandled_error(e)


class ProjectController(RestController):

    membership = MembershipController()

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 15

    def set_cache(self, values):
        token = request.cookies.get('auth_pubtkt')
        if token:
            self.cache[token] = (time.time(), values)

    def get_cache(self):
        token = request.cookies.get('auth_pubtkt')
        if token:
            last, values = self.cache.get(token, (None, None))
            if last and last + self.cache_timeout > time.time():
                return values

    @expose()
    def get(self):
        projects = self.get_cache()
        if projects:
            return json.dumps(projects)
        projects = {}

        for p in gerrit.get_projects():
            projects[p] = {'open_reviews': 0, 'open_issues': 0, 'admin': 0}

        for p in gerrit.get_projects_by_user():
            projects[p]['admin'] = 1

        for issue in redminec.get_open_issues().get('issues'):
            prj = issue.get('project').get('name')
            if prj in projects:
                projects[prj]['open_issues'] += 1

        for review in gerrit.get_open_changes():
            prj = review.get('project')
            if prj in projects:
                projects[prj]['open_reviews'] += 1
        self.set_cache(projects)
        return json.dumps(projects)

    @expose()
    def put(self, name=None):
        if not name:
            abort(400)
        try:
            # create project
            inp = request.json if request.content_length else {}
            gerrit.init_project(name, inp)
            redminec.init_project(name, inp)
            response.status = 201
            self.set_cache(None)
            return "Project %s has been created." % name
        except Exception, e:
            return report_unhandled_error(e)

    @expose()
    def delete(self, name=None):
        if name == 'config':
            response.status = 400
            return "Deletion of config project denied"
        if not name:
            abort(400)
        try:
            # delete project
            gerrit.delete_project(name)
            redminec.delete_project(name)
            response.status = 200
            self.set_cache(None)
            return "Project %s has been deleted." % name
        except Exception, e:
            return report_unhandled_error(e)


class RootController(object):
    project = ProjectController()
    replication = ReplicationController()
    backup = BackupController()
    restore = RestoreController()
