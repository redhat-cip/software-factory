import subprocess
import os
import sys


def setUpPackage():
    print "setUpPackage!"
    if "--skip-bootstrap" in sys.argv:
        print "No bootstrap"
        return
    os.chdir("lxc")
    subprocess.call(['./bootstrap-lxc.sh'])
    os.chdir("..")


def tearDownPackage():
    print "tearDownPackage!"
    if "--skip-bootstrap" in sys.argv:
        print "No bootstrap"
        return
    os.chdir("lxc")
    subprocess.call(['./bootstrap-lxc.sh', 'stop'])
    os.chdir("..")
