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

from pecan import conf
from pecan import abort
from pecan import request
from managesf.controllers.utils import send_request, \
    template, admin_auth_cookie

import json
import logging

logger = logging.getLogger(__name__)


def create_project(name, description, private):
    logger.debug(' [redmine] create project ' + name)
    pub = 'false' if private else 'true'
    data = file(template('redmine_project_create.xml')).read() % {
        'name': name,
        'description': description,
        'identifier': name.lower(),
        'is_public': pub}

    url = "http://%(redmine_host)s/projects.json" % \
          {'redmine_host': conf.redmine['host']}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key'],
               'Content-type': 'application/xml'}
    send_request(url, [201], method='POST', data=data, headers=headers,
                 cookies=admin_auth_cookie())


def get_current_user_id():
    logger.debug(' [redmine] Fetching id of the current user')
    url = "http://%(redmine_host)s/users/current.json" % \
          {'redmine_host': conf.redmine['host']}

    resp = send_request(url, [200], method='GET')
    return resp.json()['user']['id']


def get_user_id(name):
    logger.debug(' [redmine] Fetching id for the user ' + name)
    url = "http://%(redmine_host)s/users.json?name=%(user_name)s" % \
          {'redmine_host': conf.redmine['host'],
           'user_name': name}

    headers = {'X-Redmine-API-Key': conf.redmine['api_key']}
    resp = send_request(url, [200], method='GET', headers=headers,
                        cookies=admin_auth_cookie())

    j = resp.json()
    if j['total_count'] == 0:
        abort(404)

    return j['users'][0]['id']


def get_role_id(role_name):
    logger.debug(' [redmine] fetching id of role ' + role_name)
    url = "http://%(redmine_host)s/roles.json" % \
          {'redmine_host': conf.redmine['host']}
    resp = send_request(url, [200], method='GET')
    roles = resp.json()['roles']
    for r in roles:
        if r['name'] == role_name:
            return r['id']

    return None


def edit_membership(prj_name, memberships):
    logger.debug(' [redmine] editing membership for the project')

    for m in memberships:
        data = json.dumps({"membership": m})
        url = "http://%(redmine_host)s/projects/%(pid)s/memberships.json" % \
              {'redmine_host': conf.redmine['host'],
               'pid': prj_name}
        headers = {'X-Redmine-API-Key': conf.redmine['api_key'],
                   'Content-type': 'application/json'}
        send_request(url, [201], method='POST', data=data, headers=headers,
                     cookies=admin_auth_cookie())


def update_project_roles(name, ptl, core, dev):
    memberships = []
    mgr_role_id = get_role_id('Manager')
    dev_role_id = get_role_id('Developer')

    # core user and dev user will inherit
    # of the Developer role
    dev.extend(core)

    cu = request.remote_user
    if cu not in ptl:
        ptl.append(cu)
    if cu not in dev:
        dev.append(cu)

    append = lambda x, y: memberships.append({'user_id': x, 'role_ids': y})
    for m in ptl:
        uid = get_user_id(m)
        role_id = [mgr_role_id]
        if m in dev:
            role_id.append(dev_role_id)
            del dev[dev.index(m)]
        append(uid, role_id)

    for m in dev:
        append(get_user_id(m), [dev_role_id])

    edit_membership(name, memberships)


def init_project(name, inp):
    description = '' if 'description' not in inp else inp['description']
    ptl = [] if 'ptl-group-members' not in inp else inp['ptl-group-members']
    private = False if 'private' not in inp else inp['private']
    core = [] if 'core-group-members' not in inp else inp['core-group-members']
    dev = [] if 'dev-group-members' not in inp else inp['dev-group-members']

    #create the project
    create_project(name, description, private)
    update_project_roles(name, ptl, core, dev)


def user_manages_project(prj_name):
    logger.debug(' [redmine] checking if user manages project')
    url = "http://%(redmine_host)s/projects/%(name)s/memberships.json" % \
          {'redmine_host': conf.redmine['host'],
           'name': prj_name.lower()}

    resp = send_request(url, [200], method='GET')
    membership = resp.json()['memberships']
    uid = get_current_user_id()

    manager = False
    for m in membership:
        if m['user']['id'] == uid:
            for r in m['roles']:
                if r['name'] == 'Manager':
                    manager = True
                    break
        if manager:
            break

    return manager


def delete_project(name):
    if not user_manages_project(name):
        abort(403)
    logger.debug(' [redmine] deleting project ' + name)
    url = "http://%(redmine_host)s/projects/%(project_id)s.xml" % \
          {'redmine_host': conf.redmine['host'],
           'project_id': name.lower()}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key']}
    send_request(url, [200], method='DELETE', headers=headers,
                 cookies=admin_auth_cookie())
