from gerritlib import gerrit

import os
import re
import shlex
import shutil
import subprocess
import sys
import stat


class CustomGerritClient(gerrit.Gerrit):
    def createProject(self, project, require_change_id=True):
        cmd = 'gerrit create-project'
        if require_change_id:
            cmd = '%s --require-change-id' % cmd
        cmd = '%s --empty-commit --name %s' % (cmd, project)
        out, err = self._ssh(cmd)
        return err

    def createGroup(self, group, visible_to_all=True, owner=None):
        cmd = 'gerrit create-group %s' % group
        if visible_to_all:
            cmd = '%s --visible-to-all' % cmd
        if owner:
            cmd = '%s --owner %s' % (cmd, owner)
        out, err = self._ssh(cmd)
        return err

    def addInGroup(self, group, user_email):
        cmd = 'gerrit set-members %s -a %s' % (group, user_email)
        try:
            out, err = self._ssh(cmd)
        except Exception, e:
            print "Fail to add %s in group %s. Skip it !" % (user_email, group)
            print "Fail due to : %s" % e

    def getGroupUUID(self, name):
        cmd = 'gerrit ls-groups -v -m %s' % name
        out, err = self._ssh(cmd)
        uuid = out.split('\t')[1]
        return uuid

    def deleteGroup(self, name):
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

    def deleteProject(self, name):
        cmd = 'deleteproject delete %s --force --yes-really-delete' % name
        out, err = self._ssh(cmd)
        return err


class GerritRepo(object):
    def __init__(self, infos):
        self.infos = infos
        self.infos['localcopy_path'] = '/tmp/clone-%(name)s' % self.infos
        if os.path.isdir(self.infos['localcopy_path']):
            shutil.rmtree(self.infos['localcopy_path'])
        self.email = "%(admin)s <%(email)s>" % self.infos
        ssh_wrapper = "ssh -o StrictHostKeyChecking=no -i " % self.infos + \
                      "%(gerrit-keyfile)s \"$@\"" % self.infos
        file('/tmp/ssh_wrapper.sh', 'w').write(ssh_wrapper)
        os.chmod('/tmp/ssh_wrapper.sh', stat.S_IRWXU)
        self.env = os.environ.copy()
        self.env['GIT_SSH'] = '/tmp/ssh_wrapper.sh'
        # Commit will be reject by gerrit if the commiter info
        # is not a registered user (author can be anything else)
        self.env['GIT_COMMITTER_NAME'] = self.infos['admin']
        self.env['GIT_COMMITTER_EMAIL'] = self.infos['email']
        self.debug = file('/tmp/debug', 'a')

    def _exec(self, cmd, cwd=None):
        cmd = shlex.split(cmd)
        ocwd = os.getcwd()
        if cwd:
            os.chdir(cwd)
        p = subprocess.Popen(cmd, stdout=self.debug,
                             stderr=subprocess.STDOUT,
                             env=self.env, cwd=cwd)
        p.wait()
        os.chdir(ocwd)

    def clone(self):
        print("Clone repository %s" % self.infos['name'])
        cmd = "git clone ssh://%(admin)s@%(gerrit-host)s" % self.infos + \
              ":%(gerrit-host-port)s/%(name)s %(localcopy_path)s" % self.infos
        self._exec(cmd)

    def add_file(self, path, content):
        print("Add file %s to index" % path)
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
        print("Prepare push on config for repository %s" %
              self.infos['name'])
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
        print("Push on config for repository %s" %
              self.infos['name'])

    def push_master(self, paths):
        print("Prepare push on master for repository %s" %
              self.infos['name'])
        cmd = "git checkout master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        for path, content in paths.items():
            self.add_file(path, content)
        cmd = "git commit -a --author '%s' -m'ManageSF commit'" % self.email
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git push origin master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        print("Push on master for repository %s" % self.infos['name'])

    def push_master_from_git_remote(self, infos):
        remote = infos['upstream']
        print("Fetch git objects from a remote and push to master for " +
              "repository %s" % self.infos['name'])
        cmd = "git checkout master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git remote add upstream %s" % remote
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git fetch upstream"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        print("Push remote (master branch) of %s to the Gerrit repository" %
              remote)
        cmd = "git push -f origin upstream/master:master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])
        cmd = "git reset --hard origin/master"
        self._exec(cmd, cwd=self.infos['localcopy_path'])


def populate_groups(gerrit_client, infos):
    for kgn, kgnm in [('ptl-group', 'ptl-group-members'),
                      ('core-group', 'core-group-members')]:
        try:
            members = infos[kgnm].split()
        except KeyError:
            print "No key %s skip populate %s group." % (kgnm, kgn)
            continue
        for member in members:
            gerrit_client.addInGroup(infos[kgn], member)


def create_project(gerrit_client, infos):
    print "Creating groups (ptl, core)"
    gerrit_client.createGroup(infos['ptl-group'],
                              visible_to_all=True)
    gerrit_client.createGroup(infos['core-group'],
                              visible_to_all=True,
                              owner=infos['ptl-group'])
    print "Creating project"
    gerrit_client.createProject(infos['name'],
                                require_change_id=True)


def init_gerrit_project(gerrit_client, infos):
    create_project(gerrit_client, infos)
    infos['core-group-uuid'] = \
        gerrit_client.getGroupUUID(infos['core-group'])
    infos['ptl-group-uuid'] = \
        gerrit_client.getGroupUUID(infos['ptl-group'])
    infos['non-interactive-users'] = \
        gerrit_client.getGroupUUID('Non-Interactive')
    populate_groups(gerrit_client, infos)
    grepo = GerritRepo(infos)
    grepo.clone()
    paths = {}
    paths['project.config'] = file('templates/project.config').read() % infos
    paths['groups'] = file('templates/groups').read() % infos
    grepo.push_config(paths)
    if 'upstream' in infos:
        grepo.push_master_from_git_remote(infos)
    paths = {}
    paths['.gitreview'] = file('templates/gitreview').read() % infos
    grepo.push_master(paths)


def delete_gerrit_project(gerrit_client, infos):
    try:
        for kgn in ('core-group', 'ptl-group'):
            print "Deleting group " + infos[kgn]
            gerrit_client.deleteGroup(infos[kgn])
        print "Deleting the project " + infos['name']
        gerrit_client.deleteProject(infos['name'])
    except Exception:
        print("Error occured during project deletion")


def push_dir_in_gerrit_project(infos, target_dir, paths):
    path_content = {}
    for p in paths:
        filename = os.path.basename(p)
        with open(p) as fd:
            content = fd.read()
            path_content[os.path.join(target_dir, filename)] = content
    repo = GerritRepo(infos)
    repo.clone()
    repo.push_master(path_content)


def init_redmine_project(redmine_client, infos):
    redmine_client.projects.new(name=infos['name'],
                                description=infos['description'],
                                identifier=infos['name'])
    sys.stdout.write("done.\n")


def delete_redmine_project(redmine_client, infos):
    redmine_client.projects.delete(infos['name'])
    sys.stdout.write("done.\n")


def jenkins_init_jjb(infos, ):
    sys.stdout.write("Kick JJB on Jenkins %s ... ")
    jenkins_kick_path = '/usr/local/jenkins/slave_scripts/kick.sh'
    cmd = "ssh -i %s -o StrictHostKeyChecking=no %s@%s %s" % (
        infos['jenkins-privkey'],
        'root',
        infos['jenkins-host'],
        jenkins_kick_path)
    args = shlex.split(cmd)
    subprocess.call(args)
    sys.stdout.write("done.\n")
