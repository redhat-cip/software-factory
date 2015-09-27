#!/bin/env python

import argparse
import os
import subprocess


def execute(argv):
    print "[deploy][debug] Executing %s" % argv
    return subprocess.Popen(argv).wait()


def pread(argv):
    print "[deploy][debug] Executing %s" % argv
    return subprocess.Popen(argv, stdout=subprocess.PIPE).communicate()[0]


def virsh(argv):
    execute(["virsh", "-c", "lxc:///"] + argv)


def prepare_role(base_path, name, ip,
                 netmask="255.255.255.0", gateway="192.168.135.1"):
    print "[deploy] Prepare role %s (%s)" % (name, ip)
    if not os.path.isdir("/var/lib/lxc"):
        os.mkdir("/var/lib/lxc", 0755)
    if not os.path.isdir("/var/lib/lxc/%s" % name):
        os.mkdir("/var/lib/lxc/%s" % name, 0755)
    root = "/var/lib/lxc/%s/rootfs" % name
    if execute(["rsync", "-a", "--delete",
                "%s/softwarefactory/" % base_path,
                "%s/" % root]):
        print "Could not prepare %s with %s" % (name, base_path)
        exit(1)

    # network
    open("%s/etc/sysconfig/network-scripts/ifcfg-eth0" % root, "w").write(
        "DEVICE=eth0\n" +
        "ONBOOT=yes\n" +
        "BOOTPROTO=static\n" +
        "IPADDR=%s\n" % ip +
        "NETMASK=%s\n" % netmask +
        "GATEWAY=%s\n" % gateway
    )
    open("%s/etc/sysconfig/network" % root, "w").write(
        "NETWORKING=yes\n" +
        "HOSTNAME=%s.%s" % (name, args.domain)
    )
    open("%s/etc/hostname" % root, "w").write("%s\n" % (name))
    open("%s/etc/hosts" % root, "w").write("127.0.0.1 %s.%s %s localhost\n"
                                           % (name, args.domain, name))
    if not os.path.isdir("%s/root/.ssh" % root):
        os.mkdir("%s/root/.ssh" % root, 0755)

    # ssh access
    ssh_dir = "%s/.ssh" % os.path.expanduser("~%s" % os.environ['SUDO_USER'])
    if not os.path.isdir(ssh_dir):
        os.mkdir(ssh_dir)
        os.chmod(ssh_dir, 0700)

    if not os.path.isfile("%s/id_rsa" % ssh_dir):
        execute(["ssh-keygen", "-f", "%s/id_rsa" % ssh_dir, "-N", ""])
    open("%s/root/.ssh/authorized_keys" % root, "w").write(
        open("%s/id_rsa.pub" % ssh_dir).read()
    )

    # disable cloud-init
    s = "%s/etc/systemd/system/multi-user.target.wants/cloud-init.service" % (
        root)
    if os.path.exists(s):
        os.unlink(s)


def stop():
    print "[deploy] Stop"
    execute(["virsh", "net-destroy", "sf-net"])
    for instance in pread([
        "virsh", "-c", "lxc:///", "list", "--all", "--name"
    ]).split():
        virsh(["destroy", instance])
        virsh(["undefine", instance])


def init(base):
    print "[deploy] Init"
    prepare_role(base, "managesf", "192.168.135.101")
    if args.refarch == "2nodes-jenkins":
        prepare_role(base, "jenkins",  "192.168.135.102")


def start():
    print "[deploy] Start"
    if execute(["which", "virsh"]):
        execute(["yum", "install", "-y", "libvirt-daemon-lxc"])
        execute(["systemctl", "restart", "libvirtd"])
    virsh(["net-create", "libvirt-network.xml"])
    virsh(["create", "libvirt-managesf.xml"])
    if args.refarch == "2nodes-jenkins":
        virsh(["create", "libvirt-jenkins.xml"])
    virsh(["list"])


def destroy():
    print "[deploy] Destroy"
    stop()
    # execute(["rm", "-Rf", "/var/lib/lxc/"])


if "SUDO_USER" not in os.environ:
    print "Only root can do that, use sudo!"
    exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--domain", default="tests.dom")
parser.add_argument("--version")
parser.add_argument("--refarch", choices=[
    "1node-allinone", "2nodes-jenkins"],
    default="1node-allinone")
parser.add_argument("action", choices=[
    "start", "stop", "restart", "init", "destroy"])
args = parser.parse_args()

if args.action == "start":
    start()
elif args.action == "stop":
    stop()
elif args.action == "restart":
    stop()
    start()
elif args.action == "destroy":
    destroy()
elif args.action == "init":
    if args.version is None:
        # Extract INST path from role_configrc... needs bash evaluation here
        args.version = pread([
            "bash", "-c", ". ../../role_configrc; echo $SF_VER"]).strip()
    init("/var/lib/sf/roles/install/%s" % args.version)
    start()
