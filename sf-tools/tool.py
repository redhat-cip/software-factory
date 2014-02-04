#!/bin/env/python

import os
import random
import string
import sys
import shutil
from gerritlib import gerrit
from dulwich import client
from dulwich import repo
from dulwich import index


#TODO(fbo): Use Dulwich to push the project ACL
#TODO(fbo): Push the .gitreview file
#TODO(fbo): Use yaml file to describe a project

client.get_ssh_vendor = lambda: CustomSSHVendor(sys.argv[1])

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
        print args
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

class GerritRepo(object):
    def __init__(self, ssh_client, name):
        self.ssh_client = ssh_client
        self.name = name
        self.localcopy_path = '/tmp/clone-%s' % self.name
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
            exclude = exclude[0]
            os.unlink(os.path.join(self.local_repo.path, exclude))
            stages.append(exclude)
            
        index.build_index_from_tree(self.local_repo.path,
                                    indexfile,
                                    self.local_repo.object_store,
                                    tree)
        file(os.path.join(self.local_repo.path,
                          path), 'w').write(content)
        self.local_repo.stage(stages)
        self.local_repo.do_commit(message,
                            'fabien.boucher <fabien.boucher@enovance.com>',
                            ref=ref)
        self.ssh_client.send_pack(
            self.name,
            self.determine_wants,
            self.local_repo.object_store.generate_pack_contents)


    def push_acls(self, acls):
        self._push("refs/meta/config", "project.config",
                   acls, "Update ACLs")

    def push_gitreview(self):
        self._push("refs/heads/master", ".gitreview",
                   "", "Provide .gitreview file")

    def fetch_project(self):
        if os.path.isdir(self.localcopy_path):
            shutil.rmtree(self.localcopy_path)
        self.local_repo = repo.Repo.init(self.localcopy_path, mkdir=True)
        remote_refs = self.ssh_client.fetch(self.name, self.local_repo)
        self.local_repo["refs/meta/config"] = remote_refs["refs/meta/config"]
        self.local_repo["refs/heads/master"] = remote_refs["refs/heads/master"]

def create_project(project):
    name = project['name']
    group = project['core-group-name']
    gerrit_client.createGroup(group,
                       visible_to_all=True)
    gerrit_client.createProject(name,
                         require_change_id=True)

if __name__ == "__main__":
    keyfile = sys.argv[1]
    print "Using private key : %s" % keyfile

    gerrit_client = CustomGerritClient('198.154.188.171',
                        'fabien.boucher',
                        keyfile=keyfile)
    
    ssh_client = client.SSHGitClient('198.154.188.171',
                                     29418,
                                     'fabien.boucher')

    seed = [random.choice(string.ascii_letters) for n in xrange(3)]
    seed = "p-" + "".join(seed)
    print seed

    project = {'name': seed,
               'core-group-name' : '%s-core' % seed,
               'ACL-file-path': 'default-project.config'
              }

    create_project(project)
    grepo = GerritRepo(ssh_client, seed)
    acls = file('project.config').read()
    grepo.push_acls(acls) 
    grepo.push_gitreview() 
