#!/usr/bin/python

import unittest
import subprocess
import os

class Base(unittest.TestCase):
    pass

class Tool:
    cwd = "."
    def run(self, argv):
        old_cwd = os.getcwd()
        os.chdir(self.cwd)
        try:
            ret = subprocess.call([self.exe] + argv)
        finally:
            os.chdir(old_cwd)
        return ret

class ManageSf(Tool):
    cwd = "./tools/manage-sf"
    exe = "./manage"

class Git(Tool):
    exe = "/usr/bin/git"
