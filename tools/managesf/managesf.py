from dulwich import client
from dulwich import index
from dulwich import repo
from gerritlib import gerrit

import os
import re
import shutil
import sys


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

    def _push(self, ref, path, content, message, clean):
        indexfile = self.local_repo.index_path()
        tree = self.local_repo[ref].tree
        stages = [path]
        if clean:
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

        if path.split('/') > 1:
            d = re.sub(os.path.basename(path), '', path)
            try:
                os.makedirs(os.path.join(self.local_repo.path, d))
            except OSError:
                pass
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

    def push_file(self, branch, filename, data, clean=False):
        self._push(branch, filename, data, "Update %s" % filename, clean)

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
    grepo.push_file("refs/meta/config", "groups", groups)
    grepo.push_file("refs/meta/config", "project.config", acls)
    grepo.push_file("refs/heads/master", ".gitreview", gitreview, True)
    sys.stdout.write("done.\n")


def push_dir_in_gerrit_project(ssh_client, infos, target_dir, paths):
    path_content = {}
    for p in paths:
        filename = os.path.basename(p)
        with open(p) as fd:
            content = fd.read()
            path_content[filename] = content
    sys.stdout.write("Clone created repo %s ... " % infos['name'])
    email = "%s <%s>" % (infos['admin'], infos['email'])
    grepo = GerritRepo(ssh_client, infos['name'], email)
    sys.stdout.write("done.\n")
    for filename, content in path_content.items():
        path = os.path.join(target_dir, filename)
        sys.stdout.write("Push %s on repo %s ... " % (path, infos['name']))
        grepo.push_file("refs/heads/master", path, content)
        sys.stdout.write("done.\n")


def init_redmine_project(redmine_client, infos):
    sys.stdout.write("Create project on Remine %s ... " % infos['name'])
    redmine_client.projects.new(name=infos['name'],
                                description=infos['description'],
                                identifier=infos['name'])
    sys.stdout.write("done.\n")
