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

from pecan import expose
from pecan import abort
from pecan.rest import RestController
from pecan import request, response

from managesf.controllers import gerrit, redmine

import logging

logger = logging.getLogger(__name__)


class ReplicationController(RestController):
    #'add','rename-section'
    @expose()
    def put(self, section=None, setting=None, **kwargs):
        if section is None or ('value' not in request.json):
            logger.debug("Invalid input. Section is None")
            abort(403)
        value = request.json['value']
        gerrit.replication_apply_config(section, setting, value)
        return None

    #'unset', 'replace-all', 'remove-section'
    @expose()
    def delete(self, section=None, setting=None, **kwargs):
        if section is None:
            logger.debug("Invalid input. Section is None")
            abort(403)
        gerrit.replication_apply_config(section, setting)
        return None

    #'get-all', 'list'
    @expose('json')
    def get(self, section=None, setting=None, **kwargs):
        config = gerrit.replication_get_config(section, setting)
        return config

    @expose()
    def post(self, *args, **kwargs):
        inp = request.json if request.content_length else {}
        gerrit.replication_trigger(inp)
        return None


class ProjectController(RestController):
    @expose()
    def put(self, name, **kwargs):
        if name == '':
            abort(405)
        try:
            #create project
            inp = request.json if request.content_length else {}
            gerrit.init_project(name, inp)
            redmine.init_project(name, inp)

            response.status = 201
            return "Created"
        except:
            logger.exception('')
            raise

    @expose()
    def delete(self, name):
        if name == '':
            abort(405)
        try:
            #delete project
            gerrit.delete_project(name)
            redmine.delete_project(name)
            return None
        except:
            logger.exception('')
            raise


class RootController(object):
    project = ProjectController()
    replication = ReplicationController()
