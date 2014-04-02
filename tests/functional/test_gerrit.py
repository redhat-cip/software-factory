#!/usr/bin/python

import os
import time
import random

from utils import Base
from utils import ManageRestServer
from utils import ManageSfUtils
from utils import GerritGitUtils

USER = 'fabien.boucher'
PASSWD = 'userpass'
EMAIL = 'fabien.boucher@enovance.com'
PRIV_KEY_PATH = '/srv/SoftwareFactory/build/data/gerrit_admin_rsa'
GERRIT_HOST = 'sf-gerrit:29418'


class GerritFunctionalTests(Base):
    @classmethod
    def setUpClass(cls):
        cls.mrs = ManageRestServer()
        cls.mrs.run()
        cls.msu = ManageSfUtils('localhost', 9090)

    @classmethod
    def tearDownClass(cls):
        # We should first delete project that have been created
        cls.mrs.stop()

    def test_01_create_repository_as_admin(self):
        pname = 'p%s' % random.randint(0, 1000)
        # create the project as admin
        self.msu.createProject(pname, USER, PASSWD)
        # try to clone it as admin
        ggu = GerritGitUtils(USER, PRIV_KEY_PATH, EMAIL)
        url = "ssh://%s@%s/%s" % (USER, GERRIT_HOST, pname)
        ggu.clone(url, pname)
        # Check we were able to clone
        self.assertTrue(os.path.isdir(os.path.join(ggu.tempdir, pname)))
