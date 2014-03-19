import subprocess


def setUpPackage():
    subprocess.call(['lxc/bootstrap-lxc.sh'])


def tearDownPackage():
    subprocess.call(['lxc/bootstrap-lxc.sh', 'stop'])
