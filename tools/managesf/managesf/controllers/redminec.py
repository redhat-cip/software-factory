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

from pysflib.sfredmine import RedmineUtils

import logging

logger = logging.getLogger(__name__)


def get_client():
    return RedmineUtils(conf.redmine['url'],
                        key=conf.redmine['api_key'])


def init_project(name, inp):
    logger.info('[redmine] Create project %s' % name)
    rm = get_client()
    description = '' if 'description' not in inp else inp['description']
    ptl = [] if 'ptl-group-members' not in inp else inp['ptl-group-members']
    private = False if 'private' not in inp else inp['private']
    core = [] if 'core-group-members' not in inp else inp['core-group-members']
    dev = [] if 'dev-group-members' not in inp else inp['dev-group-members']

    # create the project
    rm.create_project(name, description, private)
    # Add current user to Manager and Developper
    uid = rm.get_user_id_by_username(request.remote_user)
    usermail = rm.r.user.get(uid).mail
    add_user_to_projectgroups(name, usermail, ['ptl-group'], owner=True)
    add_user_to_projectgroups(name, usermail, ['dev-group'])
    for m in ptl:
        add_user_to_projectgroups(name, m, ['ptl-group'])
    for m in core:
        add_user_to_projectgroups(name, m, ['core-group'])
    for m in dev:
        add_user_to_projectgroups(name, m, ['dev-group'])


def delete_project(name):
    rm = get_client()
    if not user_is_administrator() and not user_manages_project(name):
        abort(403)
    rm.delete_project(name)


def add_user_to_projectgroups(project, user, groups, owner=False):
    rm = get_client()
    for g in groups:
        if g not in ['ptl-group', 'core-group', 'dev-group']:
            abort(400)
    roles = rm.get_project_roles_for_user(
        project,
        rm.get_user_id_by_username(request.remote_user))
    logger.info("[redmine] Add user %s in groups %s from project %s" %
                (user, str(groups), project))
    uid = rm.get_user_id(user)
    role_id = []
    # only admin or manager can add manager
    if 'ptl-group' in groups:
        if (not user_is_administrator()) and ('Manager' not in roles) and \
                not owner:
            logger.info("[redmine] Aborded due to user is not admin,Manager")
            abort(401)
        mgr_role_id = rm.get_role_id('Manager')
        role_id.append(mgr_role_id)
    if ('core-group' in groups) or ('dev-group' in groups):
        if (not user_is_administrator()) and ('Manager' not in roles) and \
           ('Developer' not in roles) and not owner:
            logger.info("[redmine] Aborded due to user is not "
                        "admin,Manager,Developer")
            abort(401)
        dev_role_id = rm.get_role_id('Developer')
        role_id.append(dev_role_id)
    m = rm.get_project_membership_for_user(project, uid)
    if m:
        roles = rm.get_project_roles_for_user(project, uid)
        role_ids = [rm.get_role_id(u) for u in roles]
        role_ids.extend(role_id)
        rm.update_membership(m, role_ids)
    else:
        memberships = {'user_id': uid, 'role_ids': role_id}
        rm.update_project_membership(project, [memberships])


def delete_user_from_projectgroups(project, user, group):
    rm = get_client()
    # if user is not project member, then return
    uid = rm.get_user_id(user)
    m = rm.get_project_membership_for_user(project, uid)
    if not m:
        return None

    # get current user roles
    roles = rm.get_project_roles_for_user(
        project,
        rm.get_user_id_by_username(request.remote_user))

    # if user not requested a single group, then delete all groups,
    # otherwise delete requested group
    if group is None:
        # delete all groups
        if (not user_is_administrator()) and ('Manager' not in roles):
            logger.debug("[redmine] Aborded due to user is not admin,Manager")
            abort(401)
        rm.delete_membership(m)
    else:
        if group and group not in ['ptl-group', 'core-group', 'dev-group']:
            abort(400)
        # Get the role id from requested group name
        if group in ['dev-group', 'core-group']:
            if (not user_is_administrator()) and ('Manager' not in roles) and \
               ('Developer' not in roles):
                logger.debug(
                    "[redmine] Aborded due to user is not "
                    "admin,Manager,developer")
                abort(401)
            role_id = rm.get_role_id('Developer')
        else:
            if (not user_is_administrator()) and ('Manager' not in roles):
                logger.debug("[redmine] Aborded due to user is not "
                             "admin,Manager")
                abort(401)
            role_id = rm.get_role_id('Manager')
        # Get list of current role_ids for this user
        uroles = rm.get_project_roles_for_user(project, uid)
        role_ids = [rm.get_role_id(u) for u in uroles]
        # check if requested role is present in the membership roles
        if role_id in role_ids:
            role_ids.remove(role_id)
            # delete te requested role
            rm.update_membership(m, role_ids)


def user_manages_project(prj_name):
    rm = get_client()
    roles = rm.get_project_roles_for_user(
        prj_name,
        rm.get_user_id_by_username(request.remote_user))
    if 'Manager' in roles:
        return True
    return False


def user_is_administrator():
    return request.remote_user == conf.admin['name']


def get_open_issues():
    rm = get_client()
    return rm.get_open_issues()


def get_active_users():
    rm = get_client()
    return rm.active_users()
