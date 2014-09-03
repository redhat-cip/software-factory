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
from gerritlib import gerrit
from managesf.controllers.utils import send_request, \
    template, admin_auth_cookie
from subprocess import Popen, PIPE

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


def get_projects_by_user():
    projects = get_projects()
    if user_is_administrator():
        logger.debug(" Projects owned by user - " + " , ".join(projects))
        return projects
    names = []
    for project in projects:
        if user_owns_project(project):
            names.append(projects)
    logger.debug("projects owned by user - " + " , ".join(names))
    return names


def get_group_id(grp_name):
    logger.debug(' [gerrit] fetching group id of ' + grp_name)
    url = "http://%(gerrit_host)s/r/a/groups/%(group_name)s/detail" % \
          {'gerrit_host': conf.gerrit['host'],
           'group_name': grp_name}

    resp = send_request(url, [200],
                        method='GET',
                        cookies=admin_auth_cookie())
    return gerrit_json_resp(resp)['id']


def add_user_to_group(grp_name, user):
    logger.debug(' [gerrit] adding ' + user + ' to group ' + grp_name)
    url = "http://%(gerrit_host)s/r/a/groups/%(group_name)s/members/" \
          "%(user_name)s" % {'gerrit_host': conf.gerrit['host'],
                             'group_name': grp_name,
                             'user_name': user}
    send_request(url, [200, 201],
                 cookies=admin_auth_cookie())


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
                 cookies=admin_auth_cookie())
    add_user_to_group(grp_name, request.remote_user)


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
                 cookies=admin_auth_cookie())


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
                 cookies=admin_auth_cookie())


def get_projects():
    logger.debug(' [gerrit] fetching projects that this user belongs to')
    url = "http://%(gerrit_host)s/r/a/projects/?" % \
          {'gerrit_host': conf.gerrit['host']}

    resp = send_request(url, [200], method='GET')

    js = gerrit_json_resp(resp)

    projects = []
    for k in js:
        projects.append(k)

    return projects


def get_groups():
    logger.debug(' [gerrit] fetching groups that this user belongs to')
    url = "http://%(gerrit_host)s/r/a/accounts/self/groups" % \
          {'gerrit_host': conf.gerrit['host']}

    resp = send_request(url, [200], method='GET')

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
                        cookies=admin_auth_cookie())
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
                     {'admin': conf.admin['name'],
                      'email': conf.admin['email']}
        ssh_wrapper = "ssh -o StrictHostKeyChecking=no -i" \
                      "%(gerrit-keyfile)s \"$@\"" % \
                      {'gerrit-keyfile': conf.gerrit['sshkey_priv_path']}
        file('/tmp/ssh_wrapper.sh', 'w').write(ssh_wrapper)
        os.chmod('/tmp/ssh_wrapper.sh', stat.S_IRWXU)
        self.env = os.environ.copy()
        self.env['GIT_SSH'] = '/tmp/ssh_wrapper.sh'
        # Commit will be reject by gerrit if the commiter info
        # is not a registered user (author can be anything else)
        self.env['GIT_COMMITTER_NAME'] = conf.admin['name']
        self.env['GIT_COMMITTER_EMAIL'] = conf.admin['email']

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
        # logging std_out also logs std_error as both use same pipe
        if std_out:
            logger.debug(" [gerrit] cmd %s output" % cmd)
            logger.debug(std_out)
        os.chdir(ocwd)

    def clone(self):
        logger.debug(" [gerrit] Clone repository %s" % self.prj_name)
        cmd = "git clone ssh://%(admin)s@%(gerrit-host)s" \
              ":%(gerrit-host-port)s/%(name)s %(localcopy_path)s" % \
              {'admin': conf.admin['name'],
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

    def reload_replication_plugin(self):
        cmd = 'gerrit plugin reload replication'
        out, err = self._ssh(cmd)

    def trigger_replication(self, cmd):
        print "[gerrit] Triggering Replication"
        out, err = self._ssh(cmd)
        if err:
            logger.debug("Replication Trigger error - %s" % err)


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
        {'gerrit-host': conf.gerrit['top_domain'],
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
                if m != request.remote_user:
                    add_user_to_group(dev, m)

    create_project(name, description)
    init_git_repo(name, description, upstream, private)


def delete_project(name):
    if not user_owns_project(name) and not user_is_administrator():
        logger.debug(" [gerrit] User is neither an Administrator"
                     " nor does own project")
        abort(401)

    # user owns the project, so delete it now
    gerrit_client = CustomGerritClient(conf.gerrit['host'],
                                       conf.admin['name'],
                                       keyfile=conf.gerrit['sshkey_priv_path'])
    gerrit_client.deleteGroup(get_core_group_name(name))
    gerrit_client.deleteGroup(get_ptl_group_name(name))
    try:
        # if dev group exists, no exception will be thrown
        gerrit_client.deleteGroup(get_dev_group_name(name))
    except Exception:
        pass
    _delete_project(name)


def replication_ssh_run_cmd(subcmd):
    host = '%s@%s' % (conf.gerrit['user'], conf.gerrit['host'])
    sshcmd = ['ssh', '-o', 'LogLevel=ERROR', '-o', 'StrictHostKeyChecking=no',
              '-o', 'UserKnownHostsFile=/dev/null', '-i',
              conf.gerrit['sshkey_priv_path'], host]
    cmd = sshcmd + subcmd

    p1 = Popen(cmd, stdout=PIPE)
    return p1.communicate()


def replication_read_config():
    lines = []
    cmd = ['git', 'config', '-f', conf.gerrit['replication_config_path'], '-l']
    out, err = replication_ssh_run_cmd(cmd)
    if err:
        logger.debug(" reading config file err %s " % err)
        abort(500)
    elif out:
        logger.debug(" Contents of replication config file ... \n%s " % out)
        out = out.strip()
        lines = out.split("\n")
    config = {}
    for line in lines:
        setting, value = line.split("=")
        section = setting.split(".")[1]
        setting = setting.split(".")[2]
        if setting == 'projects':
            if (len(value.split()) != 1):
                logger.debug("Invalid Replication config file.")
                abort(500)
            elif section in config and 'projects' in config[section]:
                logger.debug("Invalid Replication config file.")
                abort(500)
        if section not in config.keys():
            config[section] = {}
        config[section].setdefault(setting, []).append(value)
    logger.debug("Contents of the config file - " + str(config))
    return config


def replication_validate(projects, config, section=None, setting=None):
    settings = ['push', 'projects', 'url', 'receivepack', 'uploadpack',
                'timeout', 'replicationDelay', 'threads']
    if setting and (setting not in settings):
        logger.debug("Setting %s is not supported." % setting)
        logger.debug("Supported settings - " + " , ".join(settings))
        abort(400)
    if len(projects) == 0:
        logger.debug("User doesn't own any project.")
        abort(403)
    if section and (section in config):
        for project in config[section]['projects']:
            if project not in projects:
                logger.debug("User unauthorized for this section %s" % section)
                abort(403)


def replication_apply_config(section, setting=None, value=None):
    projects = get_projects_by_user()
    config = replication_read_config()
    replication_validate(projects, config, section, setting)
    gitcmd = ['git', 'config', '-f', conf.gerrit['replication_config_path']]
    _section = 'remote.' + section
    if value:
        if setting:
            if setting == 'url' and ('$' in value):
                # To allow $ in url
                value = "\$".join(value.rsplit("$", 1))
            if setting == 'projects' and (section in config):
                logger.debug("Project already exist.")
                abort(400)
            cmd = ['--add', '%s.%s' % (_section, setting), value]
        else:
            cmd = ['--rename-section', _section, 'remote.%s' % value]
    elif setting:
        cmd = ['--unset-all', '%s.%s' % (_section, setting)]
    else:
        cmd = ['--remove-section', _section]
    str_cmd = " ".join(cmd)
    logger.debug(" Requested command is ... \n%s " % str_cmd)
    cmd = gitcmd + cmd
    out, err = replication_ssh_run_cmd(cmd)
    if err:
        logger.debug(" apply_config err %s " % err)
        return err
    else:
        logger.debug(" Reload the replication plugin to pick up"
                     " the new configuration")
        gerrit_client = CustomGerritClient(
            conf.gerrit['host'],
            conf.admin['name'],
            keyfile=conf.gerrit['sshkey_priv_path'])
        gerrit_client.reload_replication_plugin()


def replication_get_config(section=None, setting=None):
    projects = get_projects_by_user()
    config = replication_read_config()
    replication_validate(projects, config, section, setting)
    userConfig = {}
    # Return setting
    if setting:
        logger.debug("User GET request: %s %s" % (section, setting))
        if (section in config) and (setting in config[section]):
            userConfig[setting] = config[section][setting]
    else:
        # Return the authorized sections for the user
        logger.debug("User GET request for all sections")
        for _section in config:
            for project in config[_section]['projects']:
                if project in projects:
                    userConfig[_section] = config[_section]
                    break
    logger.debug("Config for user: %s" % str(userConfig))
    return userConfig


def replication_trigger(json):
    logger.debug("replication_trigger %s" % str(json))
    wait = True if 'wait' not in json else json['wait'] in ['True', 'true', 1]
    url = None if 'url' not in json else json['url']
    project = None if 'project' not in json else json['project']
    cmd = " replication start"
    projects = get_projects_by_user()
    config = replication_read_config()
    find_section = None
    for section in config:
        if url and 'url' in config[section]:
            if url in config[section]['url']:
                find_section = section
                cmd = cmd + " --url %s" % url
                break
        elif project and 'projects' in config[section]:
            if project in config[section]['projects']:
                find_section = section
                cmd = cmd + " %s" % project
                break
    if find_section:
        replication_validate(projects, config, find_section)
    elif wait:
        cmd = cmd + " --wait"
    elif user_is_administrator():
        cmd = cmd + " --all"
    else:
        logger.debug("Trigger replication for all projects owned by user")
        if len(projects) == 0:
            logger.debug("User doesn't own any projects, "
                         "so unauthorized to trigger repilication")
            abort(403)
        cmd = cmd + "  " + "  ".join(projects)
    logger.debug("Replication cmd - %s " % cmd)
    gerrit_client = CustomGerritClient(conf.gerrit['host'],
                                       conf.admin['name'],
                                       keyfile=conf.gerrit['sshkey_priv_path'])
    gerrit_client.trigger_replication(cmd)
