import subprocess
import os


def setUpPackage():
    print "setUpPackage!"
    if "SF_SKIP_BOOTSTRAP" in os.environ:
        print "No bootstrap"
        return
    os.chdir("lxc")
    subprocess.call(['./bootstrap-lxc.sh'])
    os.chdir("..")


def tearDownPackage():
    print "tearDownPackage!"
    if "SF_SKIP_BOOTSTRAP" in os.environ:
        print "No bootstrap"
        return
    os.chdir("lxc")
    subprocess.call(['./bootstrap-lxc.sh', 'stop'])
    os.chdir("..")
