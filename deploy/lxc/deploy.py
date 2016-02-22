#!/bin/env python

import argparse
import os
import subprocess

DEBUG = False


def execute(argv, silent=False):
    if not DEBUG and silent:
        stderr = subprocess.PIPE
    else:
        print "[deploy][debug] Executing %s" % argv
        stderr = None
    return subprocess.Popen(argv, stderr=stderr).wait()


def pread(argv, silent=False):
    if not DEBUG and silent:
        stderr = subprocess.PIPE
    else:
        print "[deploy][debug] Executing %s" % argv
        stderr = None
    return subprocess.Popen(argv,
                            stdout=subprocess.PIPE,
                            stderr=stderr).communicate()[0]


def virsh(argv, silent=False):
    execute(["virsh", "-c", "lxc:///"] + argv, silent)


def port_redirection(mode):
    if mode == "up":
        mode_arg = "-I"
        silent = False
    elif mode == "down":
        mode_arg = "-D"
        silent = True

    try:
        ext_interface = pread(["ip", "route", "get", "8.8.8.8"],
                              silent=silent).split()[4]
    except IndexError:
        raise RuntimeError("No default route available")

    execute(["iptables", mode_arg, "FORWARD", "-i", ext_interface,
             "-d", "192.168.135.101", "-j", "ACCEPT"], silent=silent)
    for port in (80, 443, 8080, 29418, 45452, 64738):
        execute(["iptables", mode_arg, "PREROUTING", "-t", "nat",
                 "-i", ext_interface, "-p", "tcp", "--dport", str(port),
                 "-j", "DNAT", "--to-destination", "192.168.135.101:%d" % port
                 ], silent=silent)
    for uport in (64738,):
        execute(["iptables", mode_arg, "PREROUTING", "-t", "nat",
                 "-i", ext_interface, "-p", "udp", "--dport", str(uport),
                 "-j", "DNAT", "--to-destination", "192.168.135.101:%d" % uport
                 ], silent=silent)


def prepare_role(base_path, name, ip,
                 netmask="255.255.255.0", gateway="192.168.135.1"):
    print "[deploy] Prepare role %s (%s)" % (name, ip)
    if not os.path.isdir("/var/lib/lxc"):
        os.mkdir("/var/lib/lxc", 0755)
    if not os.path.isdir("/var/lib/lxc/%s" % name):
        os.mkdir("/var/lib/lxc/%s" % name, 0755)
    root = "/var/lib/lxc/%s/rootfs" % name
    if execute(["rsync", "-a", "--delete",
                "--exclude", "/var/lib/sf/roles/install/",
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
        execute(["chown", os.environ['SUDO_USER'], "%s/id_rsa" % ssh_dir])
    open("%s/root/.ssh/authorized_keys" % root, "w").write(
        open("%s/id_rsa.pub" % ssh_dir).read()
    )

    # disable cloud-init
    for unit in ("cloud-init", "cloud-init-local", "cloud-config",
                 "cloud-final"):
        for p in ("etc/systemd/system/multi-user.target.wants",
                  "usr/lib/systemd/system"):
            s = "%s/%s/%s.service" % (root, p, unit)
            if os.path.exists(s):
                os.unlink(s)


def stop():
    print "[deploy] Stop"
    port_redirection("down")
    execute(["virsh", "net-destroy", "sf-net"], silent=True)
    for instance in pread([
        "virsh", "-c", "lxc:///", "list", "--all", "--name"
    ], silent=True).split():
        virsh(["destroy", instance], silent=True)
        virsh(["undefine", instance], silent=True)
    # Make sure no systemd-machinectl domain leaked
    for machine in pread(['machinectl', 'list'], silent=True).split('\n'):
        if 'libvirt-lxc' not in machine:
            continue
        execute(['machinectl', 'terminate', machine.split()[0]], silent=True)


def init(base):
    print "[deploy] Init"
    prepare_role(base, "managesf", "192.168.135.101")
    if args.refarch == "2nodes-jenkins":
        prepare_role(base, "jenkins",  "192.168.135.102")


def start():
    print "[deploy] Start"
    virsh(["net-create", "libvirt-network.xml"])
    virsh(["create", "libvirt-managesf.xml"])
    if args.refarch == "2nodes-jenkins":
        virsh(["create", "libvirt-jenkins.xml"])
    port_redirection("up")
    virsh(["list"])


def destroy():
    print "[deploy] Destroy"
    stop()
    # execute(["rm", "-Rf", "/var/lib/lxc/"])


if "SUDO_USER" not in os.environ:
    print "Only root can do that, use sudo!"
    exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--domain", default="sftests.com")
parser.add_argument("--version")
parser.add_argument("--workspace", default="/var/lib/sf")
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
        # Extracts version from role_configrc... needs bash evaluation here
        args.version = pread([
            "bash", "-c", ". ../../role_configrc; echo $SF_VER"],
            silent=True).strip()
    init("%s/roles/install/%s" % (args.workspace, args.version))
    start()
