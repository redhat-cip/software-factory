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

# We rely on https://github.com/maxtepkeev/python-redmine

import json
import requests

from redmine import Redmine
from redmine.utilities import to_string, json_response
from redmine.exceptions import (
    AuthError,
    ConflictError,
    ImpersonateError,
    ServerError,
    ValidationError,
    ResourceNotFoundError,
    RequestEntityTooLargeError,
    UnknownError
    )


class SFRedmine(Redmine):
    def __init__(self, *args, **kwargs):
        super(SFRedmine, self).__init__(*args, **kwargs)
        if 'auth_cookie' in kwargs:
            self.auth_cookie = kwargs['auth_cookie']
        else:
            self.auth_cookie = None

    def request(self, method, url, headers=None, params=None,
                data=None, raw_response=False):
        """Makes requests to Redmine and returns result in json format"""
        kwargs = dict(self.requests, **{
            'headers': headers or {},
            'params': params or {},
            'data': data or {},
        })

        if 'Content-Type' not in kwargs['headers'] and method in ('post',
                                                                  'put'):
            kwargs['data'] = json.dumps(data)
            kwargs['headers']['Content-Type'] = 'application/json'

        if self.impersonate is not None:
            kwargs['headers']['X-Redmine-Switch-User'] = self.impersonate

        # We would like to be authenticated by API key by default
        if self.key is not None:
            kwargs['params']['key'] = self.key
        if self.username and self.password:
            kwargs['auth'] = (self.username, self.password)
        if self.auth_cookie:
            kwargs['cookies'] = dict(auth_pubtkt=self.auth_cookie)

        response = getattr(requests, method)(url, **kwargs)

        if response.status_code in (200, 201):
            if raw_response:
                return response
            elif not response.content.strip():
                return True
            else:
                return json_response(response.json)
        elif response.status_code == 401:
            raise AuthError
        elif response.status_code == 404:
            raise ResourceNotFoundError
        elif response.status_code == 409:
            raise ConflictError
        elif response.status_code == 412 and self.impersonate is not None:
            raise ImpersonateError
        elif response.status_code == 413:
            raise RequestEntityTooLargeError
        elif response.status_code == 422:
            raise ValidationError(to_string(', '.join(
                json_response(response.json)['errors'])))
        elif response.status_code == 500:
            raise ServerError

        raise UnknownError(response.status_code)


class RedmineUtils:
    """ Utility class that eases calls on the Redmine API
    for software-factory. Provide the args you used to pass
    to python-redmine.Redmine and add auth_cookie to authenticate
    through SSO.
    """
    def __init__(self, *args, **kwargs):
        self.r = SFRedmine(*args, **kwargs)

    def project_exists(self, name):
        try:
            self.r.project.get(name)
        except ResourceNotFoundError:
            return False
        return True

    def get_issue_status(self, issueid):
        try:
            return self.r.issue.get(issueid).status
        except ResourceNotFoundError:
            return None

    def get_open_issues(self):
        url = "%s/issues.json?status_id=open" % self.r.url
        return self.r.request('get', url)

    def get_issues_by_project(self, name):
        try:
            p = self.r.project.get(name)
        except ResourceNotFoundError:
            return None
        return [i.id for i in p.issues]

    def test_issue_status(self, issueid, status):
        s = self.get_issue_status(issueid)
        if s:
            if s.name == status:
                return True
            else:
                return False

    def set_issue_status(self, iid, status_id, message=None):
        try:
            return self.r.issue.update(iid,
                                       status_id=status_id,
                                       notes=message)
        except ResourceNotFoundError:
            return None

    def create_issue(self, name, subject=''):
        issue = self.r.issue.create(project_id=name,
                                    subject=subject)
        return issue.id

    def delete_issue(self, issueid):
        try:
            return self.r.issue.delete(issueid)
        except ResourceNotFoundError:
            return None

    def check_user_role(self, name, username, role):
        for u in self.r.project_membership.filter(project_id=name):
            if self.r.user.get(u.user.id).firstname == username:
                for r in u.roles:
                    if r.name == role:
                        return True
        return False

    def create_project(self, name, description, private):
        self.r.project.create(name=name,
                              identifier=name,
                              description=description,
                              is_public='false' if private else 'true')

    def create_user(self, username, email, lastname):
        return self.r.user.create(login=username, firstname=username,
                                  lastname=lastname, mail=email)

    def get_user_id(self, mail):
        try:
            users = self.r.user.filter(mail=mail)
            for user in users:
                if user.mail == mail:
                    return user.id
        except ResourceNotFoundError:
            return None
        return None

    def get_user_id_by_username(self, username):
        try:
            users = self.r.user.filter(login=username)
            for user in users:
                if user.login == username:
                    return user.id
        except ResourceNotFoundError:
            return None
        return None

    def get_role_id(self, name):
        roles = self.r.role.all()
        for r in roles:
            if r.name == name:
                return r.id
        return None

    def get_projects(self):
        url = "%s/projects.json" % self.r.url
        return self.r.request('get', url)

    def get_project_membership_for_user(self, pname, uid):
        try:
            memb = self.r.project_membership.filter(project_id=pname)
        except ResourceNotFoundError:
            return None
        for m in memb:
            if m.user.id == uid:
                return m.id
        return None

    def get_project_roles_for_user(self, pname, uid):
        mid = self.get_project_membership_for_user(pname, uid)
        try:
            return [r['name'] for r in
                    self.r.project_membership.get(mid).roles]
        except ResourceNotFoundError:
            return []

    def update_membership(self, mid, role_ids):
        try:
            return self.r.project_membership.update(mid,
                                                    role_ids=role_ids)
        except ResourceNotFoundError:
            return None

    def update_project_membership(self, pname, memberships):
        for m in memberships:
            self.r.project_membership.create(project_id=pname,
                                             user_id=m['user_id'],
                                             role_ids=m['role_ids'])

    def delete_membership(self, id):
        try:
            return self.r.project_membership.delete(id)
        except ResourceNotFoundError:
            return None

    def delete_project(self, pname):
        try:
            return self.r.project.delete(pname)
        except ResourceNotFoundError:
            return None

    def active_users(self):
        try:
            return [(x.login, x.mail, ' '.join([x.firstname, x.lastname]))
                    for x in self.r.user.filter(status=1)]
        except ResourceNotFoundError:
            return None


# Here an usage example.
if __name__ == "__main__":
    import sfauth
    c = sfauth.get_cookie('tests.dom', 'user1', 'userpass')
    a = RedmineUtils('http://redmine.tests.dom', auth_cookie=c)
    a.create_user('fbo', 'fbo@totot.fr', 'Fabien B')
