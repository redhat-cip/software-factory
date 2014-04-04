#!/usr/bin/python

import os
import time
import config

from utils import Base
from utils import ManageRestServer
from utils import ManageSfUtils
from utils import GerritGitUtils
from utils import create_random_str

class GerritGitInterat(Base):
    """ Functional tests that interact using Git client with
    projects on Gerrit.
    """
    @classmethod
    def setUpClass(cls):
        cls.projects = []
        cls.clone_dirs = []
        cls.mrs = ManageRestServer()
        cls.mrs.run()
        cls.msu = ManageSfUtils('localhost', 9090)

    @classmethod
    def tearDownClass(cls):
        for name in cls.projects:
            cls.msu.deleteProject(name,
                                  config.ADMIN_USER,
                                  config.ADMIN_PASSWD)
        cls.mrs.stop()

    def createProject(self, name):
        self.msu.createProject(name,
                               config.ADMIN_USER,
                               config.ADMIN_PASSWD)
        self.projects.append(name)

    def test_simple_clone_as_admin(self):
        """ Verify we can clone a project as Admin user and .gitreview exist
        in the master branch
        """
        pname = 'p_%s' % create_random_str()
        self.createProject(pname)
        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.ADMIN_EMAIL)
        url = "ssh://%s@%s/%s" % (config.ADMIN_USER,
                                  config.GERRIT_HOST, pname)
        clone_dir = ggu.clone(url, pname)
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Verify master own the .gitreview file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    '.gitreview')))
        # Verify meta/config branch own both group and ACLs config file
        ggu.fetch_meta_config(clone_dir)
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'project.config')))
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    'groups')))
        
