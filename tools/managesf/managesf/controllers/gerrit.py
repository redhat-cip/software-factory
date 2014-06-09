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
from gerritlib import gerrit
from managesf.controllers.utils import send_request, template

import json
import os
import stat
import re
import shlex
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)


def gerrit_json_resp(resp):
    if not resp.text.startswith(")]}'"):
        abort(500)

    return json.loads(resp.text[4:])


def get_group_id(grp_name):
    logger.debug(' [gerrit] fetching group id of ' + grp_name)
    url = "http://%(gerrit_host)s/r/a/groups/%(group_name)s/detail" % \
          {'gerrit_host': conf.gerrit['host'],
           'group_name': grp_name}

    resp = send_request(url, [200],
                        method='GET',
                        auth=HTTPBasicAuth(conf.gerrit['admin'],
                                           conf.gerrit['http_password']))
    return gerrit_json_resp(resp)['id']


def add_user_to_group(grp_name, user):
    logger.debug(' [gerrit] adding ' + user + ' to group ' + grp_name)
    url = "http://%(gerrit_host)s/r/a/groups/%(group_name)s/members/" \
          "%(user_name)s" % {'gerrit_host': conf.gerrit['host'],
                             'group_name': grp_name,
                             'user_name': user}
    send_request(url, [200, 201],
                 auth=HTTPBasicAuth(conf.gerrit['admin'],
                                    conf.gerrit['http_password']))


def create_group(grp_name, grp_desc, prj_name):
    logger.debug(' [gerrit] creating a group ' + grp_name)
    url = "http://%(gerrit_host)s/r/a/groups/%(group_name)s" % \
          {'gerrit_host': conf.gerrit['host'],
           'group_name': grp_name}
    group_info = {
        "description": grp_desc,
        "name": grp_name,
        "visible_to_all": True
    }
    send_request(url, [201], data=json.dumps(group_info),
                 headers={'Content-type': 'application/json'},
                 auth=HTTPBasicAuth(conf.gerrit['admin'],
                                    conf.gerrit['http_password']))
    add_user_to_group(grp_name, request.remote_user['username'])


def create_project(prj_name, prj_desc):
    logger.debug(' [gerrit] creating a project ' + prj_name)
    url = "http://%(gerrit_host)s/r/a/projects/%(project_name)s" % \
          {'gerrit_host': conf.gerrit['host'],
           'project_name': prj_name}
    proj_info = {
        "description": prj_desc,
        "name": prj_name,
        "create_empty_commit": True,
        "owners": [get_ptl_group_name(prj_name)]
    }
    send_request(url, [201],
                 data=json.dumps(proj_info),
                 headers={'Content-type': 'application/json'},
                 auth=HTTPBasicAuth(conf.gerrit['admin'],
                                    conf.gerrit['http_password']))


def _delete_project(prj_name):
    logger.debug(' [gerrit] deleting project ' + prj_name)
    url = "http://%(gerrit_host)s/r/a/projects/%(project_name)s" % \
          {'gerrit_host': conf.gerrit['host'],
           'project_name': prj_name}
    data = json.dumps({"force": True})
    send_request(url, [204],
                 method='DELETE',
                 data=data,
                 headers={'Content-type': 'application/json'},
                 auth=HTTPBasicAuth(conf.gerrit['admin'],
                                    conf.gerrit['http_password']))


def get_groups():
    logger.debug(' [gerrit] fetching groups that this user belongs to')
    url = "http://%(gerrit_host)s/r/a/accounts/self/groups" % \
          {'gerrit_host': conf.gerrit['host']}

    resp = send_request(url, [200], method='GET',
                        auth=HTTPBasicAuth(request.remote_user['username'],
                                           request.remote_user['password']))

    js = gerrit_json_resp(resp)

    groups = []
    for g in js:
        groups.append(g['id'])

    return groups


def get_project_owner(pn):
    logger.debug(' [gerrit] fetching the owner group of the project ' + pn)
    url = "http://%(gerrit_host)s/r/a/access/?project=%(project)s" % \
          {'gerrit_host': conf.gerrit['host'],
           'project': pn}

    resp = send_request(url, [200],
                        method='GET',
                        auth=HTTPBasicAuth(conf.gerrit['admin'],
                                           conf.gerrit['http_password']))
    js = gerrit_json_resp(resp)
    return js[pn]['local']['refs/*']['permissions']['owner']['rules'].keys()[0]


def user_owns_project(prj_name):
    grps = get_groups()
    owner = get_project_owner(prj_name)

    return owner in grps


def user_is_administrator():
    logger.debug(' [gerrit] Checking if the user is Administrator')
    grps = get_groups()
    admin_id = get_group_id('Administrators')
    if admin_id in grps:
        return True
    return False


class GerritRepo(object):
    def __init__(self, prj_name):
        self.prj_name = prj_name
        self.infos = {}
        self.infos['localcopy_path'] = '/tmp/clone-%(name)s' % \
                                       {'name': prj_name}
        if os.path.isdir(self.infos['localcopy_path']):
            shutil.rmtree(self.infos['localcopy_path'])
        self.email = "%(admin)s <%(email)s>" % \
                     {'admin': conf.gerrit['admin'],
                      'email': conf.gerrit['admin_email']}
        ssh_wrapper = "ssh -o StrictHostKeyChecking=no -i" \
                      "%(gerrit-keyfile)s \"$@\"" % \
                      {'gerrit-keyfile': conf.gerrit['sshkey_priv_path']}
        file('/tmp/ssh_wrapper.sh', 'w').write(ssh_wrapper)
        os.chmod('/tmp/ssh_wrapper.sh', stat.S_IRWXU)
        self.env = os.environ.copy()
        self.env['GIT_SSH'] = '/tmp/ssh_wrapper.sh'
        # Commit will be reject by gerrit if the commiter info
        # is not a registered user (author can be anything else)
        self.env['GIT_COMMITTER_NAME'] = conf.gerrit['admin']
        self.env['GIT_COMMITTER_EMAIL'] = conf.gerrit['admin_email']

    def _exec(self, cmd, cwd=None):
        cmd = shlex.split(cmd)
        ocwd = os.getcwd()
        if cwd:
            os.chdir(cwd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             env=self.env, cwd=cwd)
        p.wait()
        std_out, std_err = p.communicate()
        #logging std_out also logs std_error as both use same pipe
        if std_out:
            logger.debug(" [gerrit] cmd %s output" % cmd)
            logger.debug(std_out)
        os.chdir(ocwd)

    def clone(self):
        logger.debug(" [gerrit] Clone repository %s" % self.prj_name)
        cmd = "git clone ssh://%(admin)s@%(gerrit-host)s" \
              ":%(gerrit-host-port)s/%(name)s %(localcopy_path)s" % \
              {'admin': conf.gerrit['admin'],
               'gerrit-host': conf.gerrit['host'],
               'gerrit-host-port': conf.gerrit['ssh_port'],
               'name': self.prj_name,
               'localcopy_path': self.infos['localcopy_path']
               }
        self._exec(cmd)

    def add_file(self, path, content):
        logger.debug(" [gerrit] Add file %s to index" % path)
        if path.split('/') > 1:
            d = re.sub(os.path.basename(path), '', path)
            try:
                os.makedirs(os.path.join(self.infos['localcopy_path'], d))
            except OSError:
                pass
        file(os.path.join(self.infos['localcopy_path'],
             path), 'w').write(content)
        cmd = "git add %s" % path
        self._exec(cmd, cwd=self.infos['localcopy_path'])

    def push_config(self, paths):
        logger.debug(" [gerrit] Prepare push on config for repository %s" %
                     self.prj_name)
        cmd = "git fetch origin " + \
              "refs/meta/config:refs/remotes/origin/meta/config"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git checkout meta/config"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        for path, content in paths.items():
            self.add_file(path, content)
        cmd = "git commit -a --author '%s' -m'Provides ACL and Groups'" % \
              self.email
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git push origin meta/config:meta/config"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        logger.debug(" [gerrit] Push on config for repository %s" %
                     self.prj_name)

    def push_master(self, paths):
        logger.debug(" [gerrit] Prepare push on master for repository %s" %
                     self.prj_name)
        cmd = "git checkout master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        for path, content in paths.items():
            self.add_file(path, content)
        cmd = "git commit -a --author '%s' -m'ManageSF commit'" % self.email
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git push origin master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        logger.debug(" [gerrit] Push on master for repository %s" %
                     self.prj_name)

    def push_master_from_git_remote(self, upstream):
        remote = upstream
        logger.debug(" [gerrit] Fetch git objects from a remote and push "
                     "to master for repository %s" % self.prj_name)
        cmd = "git checkout master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git remote add upstream %s" % remote
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git fetch upstream"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        logger.debug(" [gerrit] Push remote (master branch) of %s to the "
                     "Gerrit repository" % remote)
        cmd = "git push -f origin upstream/master:master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git reset --hard origin/master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])


class CustomGerritClient(gerrit.Gerrit):
    def deleteGroup(self, name):
        logger.debug(" [gerrit] deleting group " + name)
        grp_id = "select group_id from account_group_names " \
                 "where name=\"%s\"" % name
        tables = ['account_group_members',
                  'account_group_members_audit',
                  'account_group_by_id',
                  'account_group_by_id_aud',
                  'account_groups']
        for t in tables:
            cmd = 'gerrit gsql -c \'delete from %(table)s where ' \
                  'group_id=(%(grp_id)s)\'' % {'table': t, 'grp_id': grp_id}
            out, err = self._ssh(cmd)
        cmd = 'gerrit gsql -c \'delete from account_group_names ' \
              'where name=\"%s\"' % (name)
        out, err = self._ssh(cmd)


def init_git_repo(prj_name, prj_desc, upstream, private):
    grps = {}
    grps['project-description'] = prj_desc
    grps['core-group-uuid'] = get_group_id(get_core_group_name(prj_name))
    grps['ptl-group-uuid'] = get_group_id(get_ptl_group_name(prj_name))
    if private:
        grps['dev-group-uuid'] = get_group_id(get_dev_group_name(prj_name))
    grps['non-interactive-users'] = get_group_id('Non-Interactive%20Users')
    grps['core-group'] = get_core_group_name(prj_name)
    grps['ptl-group'] = get_ptl_group_name(prj_name)
    if private:
        grps['dev-group'] = get_dev_group_name(prj_name)
    grepo = GerritRepo(prj_name)
    grepo.clone()
    paths = {}

    prefix = ''
    if private:
        prefix = 'private-'
    paths['project.config'] = file(template(prefix +
                                   'project.config')).read() % grps
    paths['groups'] = file(template(prefix + 'groups')).read() % grps
    grepo.push_config(paths)
    if upstream:
        grepo.push_master_from_git_remote(upstream)
    paths = {}
    paths['.gitreview'] = file(template('gitreview')).read() % \
        {'gerrit-host': conf.gerrit['host'],
         'gerrit-host-port': conf.gerrit['ssh_port'],
         'name': prj_name
         }
    grepo.push_master(paths)


def get_core_group_name(prj_name):
    return "%s-core" % prj_name


def get_ptl_group_name(prj_name):
    return "%s-ptl" % prj_name


def get_dev_group_name(prj_name):
    return "%s-dev" % prj_name


def init_project(name, json):
    upstream = None if 'upstream' not in json else json['upstream']
    description = "" if 'description' not in json else json['description']
    private = False if 'private' not in json else json['private']

    core = get_core_group_name(name)
    core_desc = "Core developers for project " + name
    create_group(core, core_desc, name)
    if 'core-group-members' in json:
        for m in json['core-group-members']:
            add_user_to_group(core, m)

    ptl = get_ptl_group_name(name)
    ptl_desc = "Project team lead for project " + name
    create_group(ptl, ptl_desc, name)
    if 'ptl-group-members' in json:
        for m in json['ptl-group-members']:
            add_user_to_group(ptl, m)

    if private:
        dev = get_dev_group_name(name)
        dev_desc = "Developers for project " + name
        create_group(dev, dev_desc, name)
        if 'dev-group-members' in json:
            for m in json['dev-group-members']:
                if m != request.remote_user['username']:
                    add_user_to_group(dev, m)

    create_project(name, description)
    init_git_repo(name, description, upstream, private)


def delete_project(name):
    if not user_owns_project(name) and not user_is_administrator():
        logger.debug(" [gerrit] User is neither an Administrator"
                     " nor does own project")
        abort(401)

    #user owns the project, so delete it now
    gerrit_client = CustomGerritClient(conf.gerrit['host'],
                                       conf.gerrit['admin'],
                                       keyfile=conf.gerrit['sshkey_priv_path'])
    gerrit_client.deleteGroup(get_core_group_name(name))
    gerrit_client.deleteGroup(get_ptl_group_name(name))
    try:
        #if dev group exists, no exception will be thrown
        gerrit_client.deleteGroup(get_dev_group_name(name))
    except Exception:
        pass
    _delete_project(name)
