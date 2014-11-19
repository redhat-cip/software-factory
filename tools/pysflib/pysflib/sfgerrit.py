#!/usr/bin/env python
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

# We rely on https://github.com/sonyxperiadev/pygerrit

import json
import logging
from requests.exceptions import HTTPError
from pygerrit.rest import GerritRestAPI
from pygerrit.rest import _decode_response

logger = logging.getLogger(__name__)


class SFGerritRestAPI(GerritRestAPI):
    def __init__(self, *args, **kwargs):
        if 'auth_cookie' in kwargs and 'auth' not in kwargs:
            auth_cookie = kwargs['auth_cookie']
            del kwargs['auth_cookie']
            super(SFGerritRestAPI, self).__init__(*args, **kwargs)
            # Re-add the auth prefix to URL because
            # the base init remove if as we does not pass
            # the auth arg
            self.url += 'r/a/'
            self.kwargs.update(
                {"cookies": dict(
                    auth_pubtkt=auth_cookie)})
        else:
            super(SFGerritRestAPI, self).__init__(*args, **kwargs)
        self.debug_logs = set()

    def debug(self, msg):
        if msg in self.debug_logs:
            # ignore already logged message
            return
        self.debug_logs.add(msg)
        logger.debug(msg)

    def get(self, endpoint, **kwargs):
        kwargs.update(self.kwargs.copy())
        url = self.make_url(endpoint)
        self.debug("Send HTTP GET request %s with kwargs %s" %
                   (url, str(kwargs)))
        response = self.session.get(url, **kwargs)
        return _decode_response(response)

    def put(self, endpoint, **kwargs):
        kwargs.update(self.kwargs.copy())
        url = self.make_url(endpoint)
        kwargs["headers"].update(
            {"Content-Type": "application/json;charset=UTF-8"})
        self.debug("Send HTTP PUT request %s with kwargs %s" %
                   (url, str(kwargs)))
        response = self.session.put(url, **kwargs)
        return _decode_response(response)

    def post(self, endpoint, **kwargs):
        headers = None
        if 'headers' in kwargs:
            headers = kwargs['headers']
            del kwargs['headers']
        kwargs.update(self.kwargs.copy())
        kwargs["headers"].update(
            {"Content-Type": "application/json;charset=UTF-8"})
        if headers is not None:
            kwargs["headers"] = headers
        url = self.make_url(endpoint)
        self.debug("Send HTTP POST request %s with kwargs %s" %
                   (url, str(kwargs)))
        response = self.session.post(url, **kwargs)
        return _decode_response(response)

    def delete(self, endpoint, **kwargs):
        headers = None
        if 'headers' in kwargs:
            headers = kwargs['headers']
            del kwargs['headers']
        kwargs.update(self.kwargs.copy())
        if headers is not None:
            kwargs["headers"] = headers
        url = self.make_url(endpoint)
        self.debug("Send HTTP DELETE request %s with kwargs %s" %
                   (url, str(kwargs)))
        response = self.session.delete(url, **kwargs)
        return _decode_response(response)


class GerritUtils:
    """ Utility class that eases calls on the Gerrit API
    for software-factory. Provide the args you used to pass
    to pygerrit.rest.GerritRestAPI and add auth_cookie
    to authenticate through SSO.
    """
    def __init__(self, *args, **kwargs):
        self.g = SFGerritRestAPI(*args, **kwargs)

    def _manage_errors(self, e):
        if e.response.status_code == 404:
            return False
        if e.response.status_code == 409:
            return False
        else:
            raise

    # Projects related API calls #
    def project_exists(self, name):
        try:
            self.g.get('projects/%s' % name)
            return True
        except HTTPError as e:
            return self._manage_errors(e)

    def create_project(self, name, desc, owners):
        data = json.dumps({
            "description": desc,
            "name": name,
            "create_empty_commit": True,
            "owners": owners,
        })
        try:
            self.g.put('projects/%s' % name,
                       data=data)
        except HTTPError as e:
            return self._manage_errors(e)

    def delete_project(self, name, force=False):
        try:
            if force:
                data = json.dumps({"force": True})
                self.g.delete(
                    'projects/%s' % name,
                    data=data,
                    headers={"Content-Type":
                             "application/json;charset=UTF-8"})
            else:
                self.g.delete('projects/%s' % name)
        except HTTPError as e:
            return self._manage_errors(e)

    def get_project(self, name):
        try:
            return self.g.get('projects/%s' % name)
        except HTTPError as e:
            return self._manage_errors(e)

    def get_projects(self):
        return self.g.get('projects/?').keys()

    def get_project_owner(self, name):
        try:
            ret = self.g.get('access/?project=%s' % name)
            perms = ret[name]['local']['refs/*']['permissions']
            return perms['owner']['rules'].keys()[0]
        except HTTPError as e:
            return self._manage_errors(e)

    # Account related API calls #
    def get_account(self, username):
        try:
            return self.g.get('accounts/%s' % username)
        except HTTPError as e:
            return self._manage_errors(e)

    def get_my_groups_id(self):
        try:
            grps = self.g.get('accounts/self/groups')
            return [g['id'] for g in grps]
        except HTTPError as e:
            return self._manage_errors(e)

    # Groups related API calls #
    def group_exists(self, name):
        return name in self.g.get('groups/')

    def create_group(self, name, desc):
        data = json.dumps({
            "description": desc,
            "name": name,
            "visible_to_all": True
        })
        try:
            self.g.put('groups/%s' % name,
                       data=data)
        except HTTPError as e:
            return self._manage_errors(e)

    def get_group_id(self, name):
        try:
            return self.g.get('groups/%s/detail' % name)['id']
        except HTTPError as e:
            return self._manage_errors(e)

    def get_group_member_id(self, group_id, username):
        try:
            resp = self.g.get('groups/%s/members/' % group_id)
            uid = [m['_account_id'] for m in resp if
                   m['username'] == username]
            if uid:
                return uid[0]
            else:
                return None
        except HTTPError as e:
            return self._manage_errors(e)

    def get_group_owner(self, name):
        try:
            return self.g.get('groups/%s/owner' % name)['owner']
        except HTTPError as e:
            return self._manage_errors(e)

    def member_in_group(self, username, groupname):
        try:
            grp = self.g.get('groups/%s/members/%s' % (groupname,
                                                       username))
            return (len(grp) >= 1 and grp['username'] == username)
        except HTTPError as e:
            return self._manage_errors(e)

    def add_group_member(self, username, groupname):
        try:
            self.g.post('groups/%s/members/%s' % (groupname,
                                                  username),
                        headers={})
        except HTTPError as e:
            return self._manage_errors(e)

    def delete_group_member(self, groupname, username):
        try:
            self.g.delete('groups/%s/members/%s' % (groupname,
                                                    username))
        except HTTPError as e:
            return self._manage_errors(e)

    # Keys related API calls #
    def add_pubkey(self, pubkey):
        headers = {'content-type': 'plain/text'}
        response = self.g.post('accounts/self/sshkeys',
                               headers=headers,
                               data=pubkey)
        return response['seq']

    def del_pubkey(self, index):
        try:
            self.g.delete('accounts/self/sshkeys/' + str(index),
                          headers={})
        except HTTPError as e:
            return self._manage_errors(e)

    # Changes related API calls #
    def submit_change_note(self, change_id, revision_id, label, rate):
        # Label can be "Code-Review, Verified, Workflow"
        review_input = json.dumps({"labels": {label: int(rate)}})
        try:
            self.g.post('changes/%s/revisions/%s/review' %
                        (change_id, revision_id), data=review_input)
        except HTTPError as e:
            return self._manage_errors(e)

    def submit_patch(self, change_id, revision_id):
        submit = json.dumps({"wait_for_merge": True})
        try:
            ret = self.g.post('changes/%s/revisions/%s/submit' %
                              (change_id, revision_id), data=submit)
            if ret['status'] == 'MERGED':
                return True
            else:
                return False
        except HTTPError as e:
            return self._manage_errors(e)

    def get_reviewer_approvals(self, changeid, reviewer):
        try:
            resp = self.g.get('changes/%s/reviewers/%s' %
                              (changeid, reviewer))
            return resp[0]['approvals']
        except HTTPError as e:
            return self._manage_errors(e)

    def get_reviewers(self, changeid):
        try:
            resp = self.g.get('changes/%s/reviewers' % changeid)
            return [r['username'] for r in resp]
        except HTTPError as e:
            return self._manage_errors(e)

    def get_my_changes_for_project(self, project):
        try:
            changes = self.g.get(
                'changes/?q=owner:self+project:%s' % project)
            return [c['change_id'] for c in changes]
        except HTTPError as e:
            return self._manage_errors(e)

    def get_change(self, project, branch, change_id):
        try:
            changeid = "%s %s %s" % (project, branch, change_id)
            changeid = changeid.replace(' ', '~')
            return self.g.get('changes/%s' % changeid)
        except HTTPError as e:
            return self._manage_errors(e)

    def get_change_last_patchset(self, change_id):
        try:
            return self.g.get('changes/%s/?o=CURRENT_REVISION' % change_id)
        except HTTPError as e:
            return self._manage_errors(e)

    def get_labels_list_for_change(self, change_id):
        try:
            ret = self.g.get('changes/%s/?o=LABELS' % change_id)
            return ret['labels']
        except HTTPError as e:
            return self._manage_errors(e)

    # Plugins related API calls #
    def list_plugins(self):
        ret = self.g.get('plugins/?all')
        return ret.keys()

    def e_d_plugin(self, plugin, mode):
        # mode can be 'enable' or 'disable'
        try:
            response = self.g.post('plugins/%s/gerrit~%s' % (plugin, mode),
                                   headers={})
            return response
        except HTTPError as e:
            return self._manage_errors(e)


# Examples
if __name__ == "__main__":
    # Call with the SSO cookie
    import sfauth
    c = sfauth.get_cookie('tests.dom', 'user1', 'userpass')
    print c
    a = GerritUtils('http://gerrit.tests.dom', auth_cookie=c)
    # Call with a basic auth
    # from requests.auth import HTTPBasicAuth
    # auth = HTTPBasicAuth('user1', 'userpass')
    # a = GerritUtils('http://gerrit.tests.dom/api', auth=auth)
    print a.member_in_group('user1', 'config-ptl')
