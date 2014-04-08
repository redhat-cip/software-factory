#!/usr/bin/python
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

#import config
#import shutil

from utils import Base
#from utils import ManageRestServer
#from utils import ManageSfUtils
#from utils import ManageSfUtilsConfigCreator
#from utils import GerritGitUtils

#import time
#import os
#import subprocess


class JenkinsFunctionalTests(Base):
    @classmethod
    def setUpClass(cls):
        pass
#        print "[+] Creating temp data dir"
#        cls.outputs = "/tmp/sf-functests-%d" % time.time()
#        os.mkdir(cls.outputs)
#        cls.mrs = ManageRestServer()
#        cls.mrs.run()
#        cls.msu = ManageSfUtils('localhost', 9090)
#        cls.msucc = ManageSfUtilsConfigCreator()

    @classmethod
    def tearDownClass(cls):
        pass
#        print "[+] Removing temp data dir %s" % cls.outputs
#        shutil.rmtree(cls.outputs)
#        cls.mrs.stop()

    def test_010_config_init(self):
        return True
#        self.msucc.createConfigProject()
#        ggu = GerritGitUtils(config.ADMIN_USER,
#                             config.ADMIN_PRIV_KEY_PATH,
#                             config.ADMIN_EMAIL)
#        url = "ssh://%s@%s/%s" % (config.ADMIN_USER,
#                                  config.GERRIT_HOST, 'config')
#        clone_dir = ggu.clone(url, 'p-config')
#        # Test that the clone is a success
#        self.assertTrue(os.path.isdir(clone_dir))
#        for f in ('init', 'jobs', 'macros', 'projects'):
#            self.assertTrue(os.path.isfile(os.path.join(clone_dir, f)))
#
#    def test_011_config_check(self):
#        pass # TODO
#        print "create a new job wrong job"
#        print "Check if config_check put a -1 on this"
#
#    def test_012_config_update(self):
#        pass # TODO
#        print "Create a new job"
#        print "Merge the change"
#        print "Check if job is created on jenkins"
