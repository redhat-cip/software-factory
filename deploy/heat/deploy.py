#!/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License")
#
# This script render Heat template based on 'refarch'

import argparse
import os
import yaml

from sfconfig import load_refarch, render_template


def render():
    arch["arch_raw"] = yaml.dump(arch_raw, default_flow_style=False)
    for host in arch["inventory"]:
        # TODO: remove default m1.medium and find flavor automatically
        host["flavor"] = "m1.medium"
    arch["fixed_ip"] = False
    render_template("%s.hot" % filename, "software-factory.hot.j2", arch)
    # Also generate fixed_ip version
    arch["fixed_ip"] = True
    render_template("%s-fixed-ip.hot" % filename, "software-factory.hot.j2",
                    arch)


def start():
    print "NotImplemented"
    # TODO: create keypair, get network id, upload image, start stack,
    #       wait for completion


def stop():
    print "NotImplemented"


parser = argparse.ArgumentParser()
parser.add_argument("--version")
parser.add_argument("--workspace", default="/var/lib/sf")
parser.add_argument("--domain", default="sftests.com")
parser.add_argument("--arch", default="../../config/refarch/allinone.yaml")
parser.add_argument("--output")
parser.add_argument("action", choices=[
    "init", "start", "stop", "restart", "render"], default="render")
args = parser.parse_args()

try:
    arch = load_refarch(args.arch, args.domain)
    arch_raw = yaml.load(open(args.arch).read())
    filename = args.output
    if not filename:
        filename = "sf-%s" % os.path.basename(
            args.arch).replace('.yaml', '')
    if filename.endswith(".hot"):
        filename = filename[:-4]

except IOError:
    print "Invalid arch: %s" % args.arch
    exit(1)

if args.action == "start":
    start()
elif args.action == "stop":
    stop()
elif args.action == "restart":
    stop()
    start()
elif args.action == "render":
    render()
