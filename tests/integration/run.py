#!/usr/bin/python

import os
import argparse
import subprocess
import sys
import time


def fail(msg):
    sys.stderr.write("%s\n" % msg)
    exit(1)

OS_ENV = ('OS_AUTH_URL', 'OS_USERNAME', 'OS_PASSWORD', 'OS_TENANT_NAME')


def pread(cmd):
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    if p.wait():
        fail("%s: failed rc %d" % (" ".join(cmd), p.returncode))
    return p.stdout.read().split("\n")


def get_ip():
    p = pread("ip addr show dev br-ex")
    bridge_ip = filter(lambda x: "inet " in x, p)[0].split()[1]
    return bridge_ip.split('/')[0]


def get_swift_base_url():
    # Get swift base url
    p = pread("openstack catalog show object-store")
    return filter(lambda x: "publicURL" in x, p)[0].split()[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Show environment variables",
                        action="store_const", const=True)
    parser.add_argument("--host", help="Deployment hostname",
                        metavar='host', default='sftests.com')
    parser.add_argument("--password", help="Admin password",
                        metavar='pass', default='userpass')
    parser.add_argument("--project", help="Project name",
                        metavar='name')
    parser.add_argument("--playbook", help="Playbook path",
                        metavar='name', default="zuul")

    parser.add_argument("--container", help="Swift container name",
                        metavar='name', default='sflogs')

    parser.add_argument("--os_base_image", help="Nodepool base image name",
                        metavar='name')
    parser.add_argument("--os_pool", help="floating ip pool",
                        metavar='name', default="external_network")
    parser.add_argument("--os_user", help="Change username and project name",
                        metavar='name')

    args = parser.parse_args()

    start_time = time.time()
    pbname = os.path.basename(args.playbook).replace(".yaml", "")
    cmd = "stdbuf -oL -eL ansible-playbook -v -i inventory %s.yaml" % pbname

    # check required environment variables
    os.environ["PATH"] = "/sbin:/bin:/usr/bin:/usr/local/bin:/usr/sbin"
    os.environ["SF_PASSWORD"] = args.password
    os.environ["SF_FQDN"] = args.host
    if not args.project:
        args.project = "it_%s" % pbname
    os.environ["SF_PROJECT"] = args.project
    os.environ["OS_NODEPOOL_BASE_IMAGE"] = str(args.os_base_image)

    os.environ["OS_CONTAINER"] = args.container
    os.environ["OS_POOL"] = args.os_pool

    if args.os_user:
        os.environ["OS_USERNAME"] = args.os_user
        os.environ["OS_TENANT_NAME"] = args.os_user

    if pbname in ("nodepool", "swiftlogs", "alltogether"):
        for key in OS_ENV:
            if key not in os.environ:
                fail("%s: required environment variable" % key)
        if "localhost" in os.environ["OS_AUTH_URL"]:
            # TempFix auth url to be accessible from instance
            os.environ["OS_AUTH_URL"] = "http://%s:5000/v2.0" % get_ip()
    if pbname == "swiftlogs":
        os.environ["OS_SWIFTURL"] = get_swift_base_url()
    if pbname == "nodepool" and not args.os_base_image:
        fail("--base_image required for nodepool test")

    if args.debug:
        print "~~~~~~~~~~~ DEBUG ~~~~~~~~~~~"
        for var in os.environ:
            if var.startswith("SF_") or var.startswith("OS_"):
                print "export %s=%s" % (var, os.environ[var])
        print " ".join(sys.argv)
        print "~~~~~~~ END DEBUG ~~~~~~~~~~~"

    # clean env
    for i in ("http_proxy", "https_proxy"):
        if i in os.environ:
            del os.environ[i]

    # chdir to ansible directory
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    if args.host != "sftests.com":
        open("inventory", "w").write("[managesf]\n%s\n" % args.host)
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "~~~~~~~~~~~ Integration tests: %s" % pbname
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    sys.stdout.flush()
    res = subprocess.Popen(cmd.split()).wait()
    elapsed = time.time() - start_time
    s = s = "SUCCESS: " if res == 0 else "FAILED: "
    print "----------> %s%s took %02.2f minutes" % (s, pbname, elapsed / 60.)
    print
    exit(res)

if __name__ == "__main__":
    main()
