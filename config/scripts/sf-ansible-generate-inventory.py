#!/usr/bin/python
# Licensed under the Apache License, Version 2.0
#
# Generate ansible inventory based on refarch

import argparse
import os
import yaml

from utils_refarch import load_refarch
from utils_refarch import render_jinja2_template


def install():
    # Add sfconfig.yaml to all group_vars
    if not os.path.isdir("%s/group_vars" % ansible_root):
        os.mkdir("%s/group_vars" % ansible_root, 0700)
    if not os.path.islink("%s/group_vars/all.yaml" % ansible_root):
        os.symlink("/etc/puppet/hiera/sf/sfconfig.yaml",
                   "%s/group_vars/all.yaml" % ansible_root)


def get_puppet_modules(role):
    role_conf = "%s/roles/sf-%s/defaults/main.yml" % (ansible_root, role)
    modules = []
    if os.path.exists(role_conf):
        d = yaml.load(open(role_conf).read())
        if d and "puppet_modules" in d:
            if not isinstance(d["puppet_modules"], list):
                d["puppet_modules"] = [d["puppet_modules"]]
            modules = map(lambda x: "::%s" % x, d["puppet_modules"])
    return modules


def generate_inventory():
    arch = load_refarch(args.arch, args.domain, args.install_server_ip)

    # Adds puppet module to architecture
    for host in arch["inventory"]:
        host["rolesname"] = map(lambda x: "sf-%s" % x, host["roles"])
        puppet_modules = set()
        for role in host["roles"]:
            for module in get_puppet_modules(role):
                puppet_modules.add(module)
        host["puppet_statement"] = "include %s" % (", ".join(puppet_modules))

    # Generate inventory
    if args.verify:
        print "==== %s ===" % args.arch
        print "\n#----8<----\n# Inventory"
        output = "/dev/stdout"
    else:
        output = "%s/hosts" % ansible_root
    render_jinja2_template(output,
                           "%s/templates/inventory.j2" % ansible_root,
                           arch)

    # Generate inventory
    if args.verify:
        print "==== %s ===" % args.arch
        print "\n#----8<----\n# get_logs playbook"
        output = "/dev/stdout"
    else:
        output = "%s/get_logs.yml" % ansible_root
    render_jinja2_template(output,
                           "%s/templates/get_logs.yml.j2" % ansible_root,
                           arch)

    # Generate main playbook
    if args.verify:
        print "\n#----8<----\n# Playbook"
    else:
        output = "%s/sf_setup.yml" % ansible_root
    render_jinja2_template(output,
                           "%s/templates/sf_setup.yml.j2" % ansible_root,
                           arch)

    if args.verify:
        print "\n#----8<----\n# Playbook"
    else:
        output = "%s/sf_postconf.yml" % ansible_root
    render_jinja2_template(output,
                           "%s/templates/sf_postconf.yml.j2" % ansible_root,
                           arch)

    if args.verify:
        print "\n#----8<----\n# Config-update Playbook"
    else:
        output = "%s/sf_configrepo_update.yml" % ansible_root
    render_jinja2_template(output,
                           "%s/templates/sf_configrepo_update.yml.j2" % (
                               ansible_root),
                           arch)

    if args.verify:
        print "\n#----8<----\n# Serverspec"
    else:
        output = "/etc/serverspec/hosts.yaml"
    render_jinja2_template(output,
                           "%s/templates/serverspec.yml.j2" % ansible_root,
                           arch)

    if not args.verify and args.arch == "/etc/puppet/hiera/sf/arch.yaml":
        # Write updated version of refarch to _arch.yaml
        open("/etc/puppet/hiera/sf/_arch.yaml", "w").write(
            yaml.dump(arch, default_flow_style=False))

        # Update /etc/hosts
        render_jinja2_template("/etc/hosts",
                               "%s/templates/etc-hosts.j2" % ansible_root,
                               arch)


parser = argparse.ArgumentParser()
parser.add_argument("--domain", default="sftests.com")
parser.add_argument("--ansible_root", default="/etc/ansible")
parser.add_argument("--verify", action='store_const', const=True)
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

if not args.verify:
    install()

generate_inventory()
