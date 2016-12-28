#!/usr/bin/python
# Licensed under the Apache License, Version 2.0
#
# Generate ansible inventory based on refarch

import argparse
import os
import yaml

from utils_refarch import load_refarch
from utils_refarch import render_jinja2_template


def generate_inventory():
    arch = load_refarch(args.arch, args.domain, args.install_server_ip)

    # Adds playbooks to architecture
    for host in arch["inventory"]:
        host["rolesname"] = map(lambda x: "sf-%s" % x, host["roles"])

    # Generate inventory
    render_jinja2_template("%s/hosts" % ansible_root,
                           "%s/templates/inventory.j2" % ansible_root,
                           arch)

    # Generate inventory
    render_jinja2_template("%s/get_logs.yml" % ansible_root,
                           "%s/templates/get_logs.yml.j2" % ansible_root,
                           arch)

    # Generate main playbook
    render_jinja2_template("%s/sf_setup.yml" % ansible_root,
                           "%s/templates/sf_setup.yml.j2" % ansible_root,
                           arch)

    render_jinja2_template("%s/sf_postconf.yml" % ansible_root,
                           "%s/templates/sf_postconf.yml.j2" % ansible_root,
                           arch)

    render_jinja2_template("%s/sf_backup.yml" % ansible_root,
                           "%s/templates/sf_backup.yml.j2" % ansible_root,
                           arch)

    render_jinja2_template("%s/sf_restore.yml" % ansible_root,
                           "%s/templates/sf_restore.yml.j2" % ansible_root,
                           arch)

    render_jinja2_template("%s/sf_configrepo_update.yml" % ansible_root,
                           "%s/templates/sf_configrepo_update.yml.j2" % (
                               ansible_root),
                           arch)

    render_jinja2_template("/etc/serverspec/hosts.yaml",
                           "%s/templates/serverspec.yml.j2" % ansible_root,
                           arch)

    if args.arch == "/etc/software-factory/arch.yaml":
        # Write updated version of refarch to _arch.yaml
        open("/etc/software-factory/_arch.yaml", "w").write(
            yaml.dump(arch, default_flow_style=False))

        # Update /etc/hosts
        render_jinja2_template("/etc/hosts",
                               "%s/templates/etc-hosts.j2" % ansible_root,
                               arch)


parser = argparse.ArgumentParser()
parser.add_argument("--domain", default="sftests.com")
parser.add_argument("--ansible_root", default="/etc/ansible")
parser.add_argument("--install_server_ip")
parser.add_argument("arch", help="refarch file")
args = parser.parse_args()

# Look for ansible directory
ansible_root = None
for path in (args.ansible_root, "../ansible", "config/ansible"):
    if os.path.isfile("%s/templates/inventory.j2" % path):
        ansible_root = path
        # Directory found, stop looking
        break
if not ansible_root:
    print "Can't find ansible directory, use --ansible_root"
    exit(1)

generate_inventory()
