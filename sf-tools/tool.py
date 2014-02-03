#!/bin/env/python

import random
import string
import sys
from gerritlib import gerrit

keyfile = sys.argv[1]

#TODO(fbo): Use Dulwich to push the project ACL
#TODO(fbo): Push the .gitreview file
#TODO(fbo): Use yaml file to describe a project

def create_project(project):
    name = project['name']
    group = project['core-group-name']
    client.createGroup(group,
                       visible_to_all=True)
    client.createProject(name,
                         require_change_id=True)

if __name__ == "__main__":
    print "Using private key : %s" % keyfile

    client = gerrit.Gerrit('198.154.188.171',
                        'fabien.boucher',
                        keyfile=keyfile)

    seed = [random.choice(string.ascii_letters) for n in xrange(3)]
    seed = "p-" + "".join(seed)

    project = {'name': seed,
               'core-group-name' : '%s-core' % seed,
               'ACL-file-path': 'default-project.config'
              }

    create_project(project)
