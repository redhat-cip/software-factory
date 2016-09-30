#!/usr/bin/python

import yaml
import os
import sys

from jinja2 import FileSystemLoader
from jinja2.environment import Environment


required_roles = (
    "install-server",
    "gateway",
    "mysql",
    "gerrit",
)


def fail(msg):
    print >>sys.stderr, msg
    exit(1)


def load_refarch(filename, domain=None, install_server_ip=None):
    arch = yaml.load(open(filename).read())
    # Update domain
    if domain:
        arch["domain"] = domain
    # roles is a dictwith roles name as key and host list as value
    arch["roles"] = {}
    # hosts_files is a dict with host ip as key and hostname list as value
    arch["hosts_file"] = {}
    # ip_prefix is used as network cidr, it's the first 3 bytes of all ips
    ip_prefix = None
    hostid = 10
    for host in arch["inventory"]:
        if install_server_ip and "install-server" in host["roles"]:
            host["ip"] = install_server_ip
        elif "ip" not in host:
            host["ip"] = "192.168.135.1%d" % hostid

        if not ip_prefix:
            ip_prefix = '.'.join(host["ip"].split('.')[0:3])
        elif ip_prefix != '.'.join(host["ip"].split('.')[0:3]):
            fail("%s: Host is not on the correct network" % host["name"])

        host["hostname"] = "%s.%s" % (host["name"], arch["domain"])
        # aliases is a list of cname for this host.
        aliases = set((host['name'],))
        for role in host["roles"]:
            # Add host to role list
            arch["roles"].setdefault(role, []).append(host)
            # Add extra aliases for specific roles
            if role == "redmine":
                aliases.add("api-redmine.%s" % arch['domain'])
            elif role == "gateway":
                aliases.add(arch['domain'])
            elif role == "cauth":
                aliases.add("auth.%s" % arch['domain'])
            # Add role name virtual name (as cname)
            aliases.add("%s.%s" % (role, arch["domain"]))
            aliases.add(role)
        arch["hosts_file"][host["ip"]] = [host["hostname"]] + list(aliases)
        # Set minimum requirement
        host.setdefault("cpu", "1")
        host.setdefault("mem", "4")
        host.setdefault("disk", "10")
        # Add id for network device name
        host["hostid"] = hostid
        hostid += 1
    arch["ip_prefix"] = ip_prefix

    # Check roles
    for requirement in required_roles:
        if requirement not in arch["roles"]:
            fail("%s role is missing" % requirement)
        if len(arch["roles"][requirement]) > 1:
            fail("Only one instance of %s is required" % requirement)

    # Add gateway and install-server hostname/ip for easy access
    gateway_host = arch["roles"]["gateway"][0]
    install_host = arch["roles"]["install-server"][0]
    arch["gateway"] = gateway_host["hostname"]
    arch["gateway_ip"] = gateway_host["ip"]
    arch["install"] = install_host["hostname"]
    arch["install_ip"] = install_host["ip"]
    return arch


def render_jinja2_template(dest, template, data):
    with open(dest, "w") as out:
        loader = FileSystemLoader(os.path.dirname(template))
        env = Environment(trim_blocks=True, loader=loader)
        template = env.get_template(os.path.basename(template))
        out.write("%s\n" % template.render(data))
    if dest != "/dev/stdout":
        print "[+] Created %s" % dest
