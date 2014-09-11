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

    url = "http://%(redmine_host)s/redmine/projects.json" % \
          {'redmine_host': conf.redmine['host']}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key'],
               'Content-type': 'application/xml'}
    send_request(url, [201], method='POST', data=data, headers=headers,
                 cookies=admin_auth_cookie())


def get_current_user_id():
    logger.debug(' [redmine] Fetching id of the current user')
    url = "http://%(redmine_host)s/redmine/users/current.json" % \
          {'redmine_host': conf.redmine['host']}

    resp = send_request(url, [200], method='GET')
    return resp.json()['user']['id']


def get_user_id(name):
    logger.debug(' [redmine] Fetching id for the user ' + name)
    url = "http://%(redmine_host)s/redmine/users.json?name=%(user_name)s" % \
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
    url = "http://%(redmine_host)s/redmine/roles.json" % \
          {'redmine_host': conf.redmine['host']}
    resp = send_request(url, [200], method='GET')
    roles = resp.json()['roles']
    for r in roles:
        if r['name'] == role_name:
            return r['id']

    return None


def update_membership(mid, role_ids):
    logger.debug(' [redmine] updating membership for the project')

    data = json.dumps({"membership": {"role_ids": role_ids}})
    url = "http://%(rh)s/redmine//memberships/%(id)s.json" % \
          {'rh': conf.redmine['host'],
           'id': mid}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key'],
               'Content-type': 'application/json'}
    send_request(url, [200], method='PUT', data=data, headers=headers,
                 cookies=admin_auth_cookie())


def edit_membership(prj_name, memberships):
    logger.debug(' [redmine] editing membership for the project ' + prj_name)

    for m in memberships:
        data = json.dumps({"membership": m})
        url = "http://%(rh)s/redmine/projects/%(pid)s/memberships.json" % \
              {'rh': conf.redmine['host'],
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

    # create the project
    create_project(name, description, private)
    update_project_roles(name, ptl, core, dev)


def add_user_to_projectgroups(project, user, groups):
    for g in groups:
        if g not in ['ptl-group', 'core-group', 'dev-group']:
            abort(400)
    memberships = []
    roles = get_project_roles_for_current_user(project)
    uid = get_user_id(user)
    role_id = []
    # only admin or manager can add manager
    if 'ptl-group' in groups:
        if (not user_is_administrator()) and ('Manager' not in roles):
            logger.debug(" [gerrit] User is not admin,Manager")
            abort(401)
        mgr_role_id = get_role_id('Manager')
        role_id.append(mgr_role_id)
    if ('core-group' in groups) or ('dev-group' in groups):
        if (not user_is_administrator()) and ('Manager' not in roles) and \
           ('Developer' not in roles):
            logger.debug(" [gerrit] User is not admin,Manager,Developer")
            abort(401)
        dev_role_id = get_role_id('Developer')
        role_id.append(dev_role_id)
    # if user already a project member, then update roles
    m = get_project_membership_for_user(project, uid)
    if m is None:
        memberships = [{'user_id': uid, 'role_ids': role_id}]
        edit_membership(project, memberships)
    else:
        update_membership(m['id'], role_id)


def delete_user_from_projectgroups(project, user, group):
    # if user is not project member, then return
    uid = get_user_id(user)
    m = get_project_membership_for_user(project, uid)
    if m is None:
        return None

    # get current user roles
    roles = get_project_roles_for_current_user(project)

    # if user not requested a single group, then delete all groups,
    # otherwise delete requested group
    if group is None:
        # delete all groups
        if (not user_is_administrator()) and ('Manager' not in roles):
            logger.debug(" [gerrit] User is not admin,Manager")
            abort(401)
        delete_membership(m['id'])
    else:
        if group and group not in ['ptl-group', 'core-group', 'dev-group']:
            abort(400)
        # Get the role id from requested group name
        if group in ['dev-group', 'core-group']:
            if (not user_is_administrator()) and ('Manager' not in roles) and \
               ('Developer' not in roles):
                logger.debug(" [gerrit] User is not admin,Manager,developer")
                abort(401)
            role_id = get_role_id('Developer')
        else:
            if (not user_is_administrator()) and ('Manager' not in roles):
                logger.debug(" [gerrit] User is not admin,Manager")
                abort(401)
            role_id = get_role_id('Manager')
        # Get list of current role_ids for this user
        role_ids = []
        for r in m['roles']:
            role_ids.append(r['id'])
        # check if requested role is present in the membership roles
        if role_id in role_ids:
            role_ids.remove(role_id)
            # delete te requested role
            update_membership(m['id'], role_ids)


def get_project_membership_for_user(prj_name, uid):
    logger.debug(' [redmine] Get project membership for user')
    url = "http://%(rh)s/redmine/projects/%(name)s/memberships.json" % \
          {'rh': conf.redmine['host'],
           'name': prj_name.lower()}

    resp = send_request(url, [200], method='GET')
    membership = resp.json()['memberships']

    user_membership = None
    for m in membership:
        if m['user']['id'] == uid:
            user_membership = m
            break

    return user_membership


def get_project_roles_for_current_user(prj_name):
    uid = get_current_user_id()
    m = get_project_membership_for_user(prj_name, uid)
    roles = []
    # if no roles for this user, return empty list
    if m is None:
        return roles
    for r in m['roles']:
        roles.append(r['name'])

    return roles


def user_manages_project(prj_name):
    logger.debug(' [redmine] checking if user manages project')
    roles = get_project_roles_for_current_user(prj_name)
    if 'Manager' in roles:
        return True
    return False


def user_is_administrator():
    return request.remote_user == conf.admin['name']


def delete_membership(id):
    logger.debug(' [redmine] deleting membership ')
    url = "http://%(redmine_host)s/redmine/memberships/%(membership_id)s.xml" % \
          {'redmine_host': conf.redmine['host'],
           'membership_id': id}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key']}
    send_request(url, [200], method='DELETE', headers=headers,
                 cookies=admin_auth_cookie())


def delete_project(name):
    if not user_is_administrator() and not user_manages_project(name):
        abort(403)
    logger.debug(' [redmine] deleting project ' + name)
    url = "http://%(redmine_host)s/redmine/projects/%(project_id)s.xml" % \
          {'redmine_host': conf.redmine['host'],
           'project_id': name.lower()}
    headers = {'X-Redmine-API-Key': conf.redmine['api_key']}
    send_request(url, [200], method='DELETE', headers=headers,
                 cookies=admin_auth_cookie())
