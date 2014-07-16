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
