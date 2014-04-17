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
from requests.auth import HTTPBasicAuth
from managesf.controllers.utils import send_request, template

import json


def create_project(name, description):
    print ' [redmine] create project ' + name
    data = file(template('redmine_project_create.xml')).read() % {
        'name': name,
        'description': description,
        'identifier': name}

    url = "http://%(redmine_host)s/projects.json" % \
          {'redmine_host': conf.redmine['host']}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key'],
               'Content-type': 'application/xml'}
    send_request(url, [201], method='POST', data=data, headers=headers)


def login_user(name, password="userpass"):
    if name.find('@') != -1:
        user_name, domain = name.split('@')
        name = user_name
    print(' [redmine] login user ' + name)
    data = json.dumps({"username": name, "password": password})
    url = "http://%(redmine_host)s/login" % \
          {'redmine_host': conf.redmine['host']}
    headers = {'Content-type': 'application/json'}
    send_request(url, [200], method='POST', data=data, headers=headers)


def get_current_user_id():
    login_user(request.remote_user['username'],
               request.remote_user['password'])
    print ' [redmine] Fetching id of the current user'
    url = "http://%(redmine_host)s/users/current.json" % \
          {'redmine_host': conf.redmine['host']}

    resp = send_request(url, [200], method='GET',
                        auth=HTTPBasicAuth(request.remote_user['username'],
                                           request.remote_user['password']))
    return resp.json()['user']['id']


def get_user_id(name):
    login_user(name)
    print ' [redmine] Fetching id for the user ' + name
    url = "http://%(redmine_host)s/users.json?name=%(user_name)s" % \
          {'redmine_host': conf.redmine['host'],
           'user_name': name}

    headers = {'X-Redmine-API-Key': conf.redmine['api_key']}
    resp = send_request(url, [200], method='GET', headers=headers)

    j = resp.json()
    if j['total_count'] == 0:
        abort(404)

    return j['users'][0]['id']


def get_role_id(role_name):
    print ' [redmine] fetching id of role ' + role_name
    url = "http://%(redmine_host)s/roles.json" % \
          {'redmine_host': conf.redmine['host']}
    resp = send_request(url, [200], method='GET',
                        auth=HTTPBasicAuth(request.remote_user['username'],
                                           request.remote_user['password']))
    roles = resp.json()['roles']
    for r in roles:
        if r['name'] == role_name:
            return r['id']

    return None


def edit_membership(prj_name, users):
    print ' [redmine] editing membership for the project'
    role_id = get_role_id('Manager')

    if role_id is None:
        print ' [redmine] Cannot find a role named Manager'
        abort(500)

    for u in users:
        membership = {
            "user_id": u,
            "role_ids": [role_id]
        }
        data = json.dumps({"membership": membership})
        url = "http://%(redmine_host)s/projects/%(pid)s/memberships.json" % \
              {'redmine_host': conf.redmine['host'],
               'pid': prj_name}
        headers = {'X-Redmine-API-Key': conf.redmine['api_key'],
                   'Content-type': 'application/json'}
        send_request(url, [201], method='POST', data=data, headers=headers)


def init_project(name, inp):
    description = '' if 'description' not in inp else inp['description']
    ptl = [] if 'ptl-group-members' not in inp else inp['ptl-group-members']

    uid = get_current_user_id()
    users = [uid]
    for m in ptl:
        users.append(get_user_id(m))

    #create the project
    create_project(name, description)
    edit_membership(name, users)


def user_manages_project(prj_name):
    print ' [redmine] checking if user manages project'
    url = "http://%(redmine_host)s/projects/%(name)s/memberships.json" % \
          {'redmine_host': conf.redmine['host'],
           'name': prj_name}

    resp = send_request(url, [200], method='GET',
                        auth=HTTPBasicAuth(request.remote_user['username'],
                                           request.remote_user['password']))
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
    print ' [redmine] deleting project ' + name
    url = "http://%(redmine_host)s/projects/%(project_id)s.xml" % \
          {'redmine_host': conf.redmine['host'],
           'project_id': name}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key']}
    send_request(url, [200], method='DELETE', headers=headers)
