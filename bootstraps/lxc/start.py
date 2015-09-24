#!/usr/bin/python

import os
import sys
import subprocess


def execute(argv):
    print "[debug] Executing %s" % argv
    return subprocess.Popen(argv).wait()


def pread(argv):
    print "[debug] Executing %s" % argv
    return subprocess.Popen(argv, stdout=subprocess.PIPE).communicate()[0]


def virsh(argv):
    execute(["virsh", "-c", "lxc:///"] + argv)


def prepare_role(name, ip, netmask="255.255.255.0", gateway="192.168.135.1"):
    print "[+] Prepare role %s (%s)" % (name, ip)
    if not os.path.isdir("/var/lib/lxc"):
        os.mkdir("/var/lib/lxc", 0755)
    if not os.path.isdir("/var/lib/lxc/%s" % name):
        os.mkdir("/var/lib/lxc/%s" % name, 0755)
    root = "/var/lib/lxc/%s/rootfs" % name
    execute(["rsync", "-a", "--delete", "%s/softwarefactory/" % base_path,
                            "%s/" % root])

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
        "HOSTNAME=%s.%s" % (name, domain_name)
    )
    open("%s/etc/hostname" % root, "w").write("%s.%s\n" % (name, domain_name))
    open("%s/etc/hosts" % root, "w").write("127.0.0.1 %s.%s %s localhost\n"
                                           % (name, domain_name, name))
    if not os.path.isdir("%s/root/.ssh" % root):
        os.mkdir("%s/root/.ssh" % root, 0755)

    # ssh access
    open("%s/root/.ssh/authorized_keys" % root, "w").write(
        open("%s/.ssh/id_rsa.pub" % os.path.expanduser(
            "~%s" % os.environ['SUDO_USER']
        )).read()
    )

    # cloud init
    open("%s/etc/cloud/cloud.cfg.d/90_cloud.cfg" % root, "w").write(
        "dsmod: local\n\n" +
        "datasource_list: [ NoCloud ]\n"
    )
    nocloud_dir = "%s/var/lib/cloud/seed/nocloud" % root
    if not os.path.isdir(nocloud_dir):
        os.makedirs(nocloud_dir)
    open("%s/meta-data" % nocloud_dir, "w").write("local-hostname: %s" % name)
    cloud_init = open("../cloudinit/%s.cloudinit" % name).read().replace(
        "SF_SUFFIX", domain_name)
    open("%s/user-data" % nocloud_dir, "w").write(cloud_init)


def stop():
    print "[+] Stop"
    execute(["virsh", "net-destroy", "sf-net"])
    for instance in pread([
        "virsh", "-c", "lxc:///", "list", "--all", "--name"
    ]).split():
        virsh(["destroy", instance])
        virsh(["undefine", instance])


def init():
    print "[+] Init"
    prepare_role("managesf", "192.168.135.54")
    # prepare_role("jenkins",  "192.168.135.55")


def start():
    print "[+] Start"
    virsh(["net-create", "libvirt-network.xml"])
    virsh(["create", "libvirt-domain-managesf.xml"])
    virsh(["list"])


def destroy():
    print "[+] Destroy"
    stop()
    # execute(["rm", "-Rf", "/var/lib/lxc/"])


def usage():
    print "usage: %s [init|destroy|start|stop|restart]" % sys.argv[0]
    exit(1)

base_path = pread(["bash", "-c", ". ../../role_configrc; echo $INST"]).strip()
domain_name = "tests.dom"

if "SUDO_USER" not in os.environ:
    print "Only root can do that, use sudo!"
    exit(1)

if len(sys.argv) != 2:
    usage()
elif sys.argv[1] == "start":
    start()
elif sys.argv[1] == "stop":
    stop()
elif sys.argv[1] == "restart":
    stop()
    start()
elif sys.argv[1] == "destroy":
    destroy()
elif sys.argv[1] == "init":
    init()
    start()
else:
    usage()
