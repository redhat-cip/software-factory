#!/bin/env python
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

import config
import os.path
import shutil

from utils import set_private_key
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import Base


def parse_project_config(project_config):
    d = {}
    d['original'] = ''
    section = ''
    for l in project_config:
        if l.strip().startswith('['):
            section = l[1:-2]
        else:
            d[section] = d.get(section, {})
            try:
                key, value = l.strip().split(' = ', 1)
                d[section][key] = d[section].get(key, [])
                d[section][key].append(value)
            except ValueError:
                # key might have empty value, like "description". Remove
                # trailing " ="
                key = l.strip()[:-2]
                d[section][key] = d[section].get(key, [])
        d['original'] += l
    return d


class TestSFACLs(Base):
    """ Functional tests that validate SF project ACLs.
    """
    @classmethod
    def setUpClass(cls):
        cls.projects = []
        cls.clone_dirs = []
        cls.dirs_to_delete = []
        cls.msu = ManageSfUtils(config.GATEWAY_URL)

    @classmethod
    def tearDownClass(cls):
        for name in cls.projects:
            cls.msu.deleteProject(name,
                                  config.ADMIN_USER)
        for dirs in cls.dirs_to_delete:
            shutil.rmtree(dirs)

    def createProject(self, name, options=None):
        self.msu.createProject(name,
                               config.ADMIN_USER,
                               options)
        self.projects.append(name)

    def test_01_validate_gerrit_project_acls(self):
        """ Verify the correct behavior of ACLs set on
        gerrit project
        """
        pname = "TestProjectACL"
        self.createProject(pname)
        un = config.ADMIN_USER
        priv_key_path = set_private_key(config.USERS[un]["privkey"])
        gitu = GerritGitUtils(un,
                              priv_key_path,
                              config.USERS[un]['email'])
        url = "ssh://%s@%s:29418/%s" % (un, config.GATEWAY_HOST,
                                        pname)
        clone_dir = gitu.clone(url, pname)
        gitu.fetch_meta_config(clone_dir)
        with open(os.path.join(clone_dir,
                               'project.config')) as project_config:
            p_config = parse_project_config(project_config)
        ptl = pname + "-ptl"
        core = pname + "-core"
        self.assertTrue('access "refs/*"' in p_config.keys(),
                        repr(p_config))
        self.assertTrue('access "refs/heads/*"' in p_config.keys(),
                        repr(p_config))
        self.assertTrue('access "refs/meta/config"' in p_config.keys(),
                        repr(p_config))
        self.assertTrue(any(ptl in l
                            for l in p_config['access "refs/*"']['owner']),
                        repr(p_config))
        self.assertTrue(any(core in l
                            for l in p_config['access "refs/*"']['read']),
                        repr(p_config))
        heads = p_config['access "refs/heads/*"']
        self.assertTrue(any(core in l
                            for l in heads['label-Code-Review']),
                        repr(p_config))
        self.assertTrue(any(core in l
                            for l in heads['label-Workflow']),
                        repr(p_config))
        self.assertTrue(any(ptl in l
                            for l in heads['label-Verified']),
                        repr(p_config))
        self.assertTrue(any(ptl in l
                            for l in heads['submit']),
                        repr(p_config))
        self.assertTrue(any(core in l
                            for l in heads['read']),
                        repr(p_config))
        # no need to test ref/meta/config, we could not test is if we
        # could not access it to begin with
        self.dirs_to_delete.append(os.path.dirname(clone_dir))
