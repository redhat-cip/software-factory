#!/bin/env/python

from dulwich import client
from dulwich import index
from dulwich import repo
from gerritlib import gerrit
from redmine import Redmine

import os
import shutil
import sys
import yaml


class CustomSSHVendor(client.SubprocessSSHVendor):
    """SSH vendor that shells out to the local 'ssh' command."""

    def __init__(self, key_path):
        self.key_path = key_path

    def run_command(self, host, command, username=None, port=None):
        import subprocess
        args = ['ssh', '-i', self.key_path, '-x']
        if port is not None:
            args.extend(['-p', str(port)])
        if username is not None:
            host = '%s@%s' % (username, host)
        args.append(host)
        proc = subprocess.Popen(args + command,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        return client.SubprocessWrapper(proc)


class CustomGerritClient(gerrit.Gerrit):
    def createProject(self, project, require_change_id=True):
        cmd = 'gerrit create-project'
        if require_change_id:
            cmd = '%s --require-change-id' % cmd
        cmd = '%s --empty-commit --name %s' % (cmd, project)
        out, err = self._ssh(cmd)
        return err

    def getGroupUUID(self, name):
        cmd = 'gerrit ls-groups -v -m %s' % name
        out, err = self._ssh(cmd)
        uuid = out.split('\t')[1]
        return uuid


class GerritRepo(object):
    def __init__(self, ssh_client, name, email):
        self.ssh_client = ssh_client
        self.name = name
        self.localcopy_path = '/tmp/clone-%s' % self.name
        self.email = email
        self.fetch_project()

    def determine_wants(self, *args):
        refs = args[0]
        refs["refs/meta/config"] = self.local_repo.refs["refs/meta/config"]
        refs["refs/heads/master"] = self.local_repo.refs["refs/heads/master"]
        return refs

    def _push(self, ref, path, content, message):
        indexfile = self.local_repo.index_path()
        tree = self.local_repo[ref].tree
        stages = [path]
        exclude = [f for f in os.listdir(self.local_repo.path)
                   if f != '.git' and f != path]
        if exclude:
            for exc in exclude:
                os.unlink(os.path.join(self.local_repo.path, exc))
                stages.append(exc)

        index.build_index_from_tree(self.local_repo.path,
                                    indexfile,
                                    self.local_repo.object_store,
                                    tree)
        file(os.path.join(self.local_repo.path,
                          path), 'w').write(content)
        self.local_repo.stage(stages)
        self.local_repo.do_commit(message,
                                  self.email,
                                  ref=ref)
        self.ssh_client.send_pack(
            self.name,
            self.determine_wants,
            self.local_repo.object_store.generate_pack_contents)

    def push_acls(self, acls):
        self._push("refs/meta/config", "project.config",
                   acls, "Update ACLs")

    def push_groups(self, groups):
        self._push("refs/meta/config", "groups",
                   groups, "Update Groups")

    def push_gitreview(self, gitreview):
        self._push("refs/heads/master", ".gitreview",
                   gitreview, "Provide .gitreview file")

    def fetch_project(self):
        if os.path.isdir(self.localcopy_path):
            shutil.rmtree(self.localcopy_path)
        self.local_repo = repo.Repo.init(self.localcopy_path, mkdir=True)
        remote_refs = self.ssh_client.fetch(self.name, self.local_repo)
        self.local_repo["refs/meta/config"] = remote_refs["refs/meta/config"]
        self.local_repo["refs/heads/master"] = remote_refs["refs/heads/master"]


def create_project(gerrit_client, infos):
    gerrit_client.createGroup(infos['core-group'],
                              visible_to_all=True)
    gerrit_client.createProject(infos['name'],
                                require_change_id=True)


def init_gerrit_project(gerrit_client, ssh_client, infos):
    sys.stdout.write("Create project %s ... " % infos['name'])
    create_project(gerrit_client, infos)
    sys.stdout.write("done.\n")
    sys.stdout.write("Retrieve groups UUID ... ")
    infos['core-group-uuid'] = \
        gerrit_client.getGroupUUID(infos['core-group'])
    infos['non-interactive-users'] = \
        gerrit_client.getGroupUUID('Non-Interactive')
    sys.stdout.write("done.\n")
    sys.stdout.write("Clone previously created repo ... ")
    email = "%s <%s>" % (infos['admin'], infos['email'])
    grepo = GerritRepo(ssh_client, infos['name'], email)
    sys.stdout.write("done.\n")
    acls = file('templates/project.config').read() % infos
    groups = file('templates/groups').read() % infos
    gitreview = file('templates/gitreview').read() % infos
    sys.stdout.write("Add ACLs, groups files, .gitreview files ... ")
    grepo.push_groups(groups)
    grepo.push_acls(acls)
    grepo.push_gitreview(gitreview)
    sys.stdout.write("done.\n")


def init_redmine_project(redmine_client, infos):
    sys.stdout.write("Create project on Remine %s ... " % infos['name'])
    redmine_client.projects.new(name=infos['name'],
                                description=infos['description'],
                                identifier=infos['name'])
    sys.stdout.write("done.\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <manage-sf.conf> <project.yaml>" % sys.argv[0]
        sys.exit(1)

    # parse manage sf configuration file
    sf_yaml = yaml.load(file(sys.argv[1]))
    sf_gerrit = [e for e in sf_yaml if
                 e.keys()[0] == 'gerrit'][0]['gerrit']
    sf_redmine = [e for e in sf_yaml if
                  e.keys()[0] == 'redmine'][0]['redmine']
    keyfile = sf_gerrit['sshkey-priv-path']
    adminuser = sf_gerrit['admin']
    adminemail = sf_gerrit['admin-email']
    gerrithost = sf_gerrit['host']
    redminehost = 'http://' + sf_redmine['host']
    redmineapikey = sf_redmine['apikey']
    redmineversion = sf_redmine['version']

    # parse project configuration file
    project_yaml = yaml.load(file(sys.argv[2]))
    name = project_yaml['name']
    desc = project_yaml['description']

    print "Will create project : %s" % name
    print "Project description : %s" % desc
    print "Using private key : %s" % keyfile
    print "Using username : %s" % adminuser
    print "Using email : %s" % adminemail
    print "Using gerrit hostname : %s" % gerrithost
    print "Using redmine hostname : %s" % redminehost
    print "Using redmine API key : %s" % redmineapikey
    print "Using redmine version : %s" % redmineversion

    gerrit_client = CustomGerritClient(gerrithost,
                                       adminuser,
                                       keyfile=keyfile)

    client.get_ssh_vendor = lambda: CustomSSHVendor(keyfile)
    ssh_client = client.SSHGitClient(gerrithost,
                                     29418,
                                     adminuser)

    redmine_client = Redmine(redminehost,
                             redmineapikey,
                             version=redmineversion)

    infos = {'name': name,
             'description': desc,
             'core-group': '%s-core' % name,
             'gerrit-host': gerrithost,
             'gerrit-host-port': '29418',
             'admin': adminuser,
             'email': adminemail,
             }

    init_gerrit_project(gerrit_client, ssh_client, infos)
    init_redmine_project(redmine_client, infos)
