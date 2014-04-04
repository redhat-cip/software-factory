import subprocess
import os

def setUpPackage():
    if "SF_SKIP_BOOTSTRAP" in os.environ:
        return
    os.chdir("lxc")
    subprocess.call(['./bootstrap-lxc.sh'])
    os.chdir("..")


def tearDownPackage():
    if "SF_SKIP_BOOTSTRAP" in os.environ:
        return
    os.chdir("lxc")
    subprocess.call(['./bootstrap-lxc.sh', 'stop'])
    os.chdir("..")
