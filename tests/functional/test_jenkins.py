#!/usr/bin/python

from utils import Base, ManageSf, Git
import time, os, subprocess

class JenkinsFunctionalTests(Base):
    @classmethod
    def setUpClass(cls):
        print "[+] Creating temp data dir"
        cls.outputs = "/tmp/sf-functests-%d" % time.time()
        os.mkdir(cls.outputs)

    @classmethod
    def tearDownClass(cls):
        print "[+] Removing temp data dir %s" % cls.outputs
        subprocess.call(["/bin/rm", "-Rf", cls.outputs])

    def test_010_config_init(self):
        print "[+] Create config repository"
        self.assertTrue(not ManageSf().run(["--action",  "init-config-repo", "--config", "manage-sf.conf"]))
        print "[+] Cloning config repository"
        self.assertTrue(not Git().run(["clone", "http://sf-gerrit/r/config", "%s/config" % self.outputs]))

    def test_011_config_check(self):
        pass # TODO
        print "create a new job wrong job"
        print "Check if config_check put a -1 on this"

    def test_012_config_update(self):
        pass # TODO
        print "Create a new job"
        print "Merge the change"
        print "Check if job is created on jenkins"
