#!/usr/bin/python
# Update hiera configuration with new defaults

from sys import argv
import yaml
import os

DEFAULT_ARCH = "/usr/local/share/sf-default-config/arch.yaml"


def save(name, data):
    filename = "%s/%s.yaml" % (hiera_dir, name)
    if os.path.isfile(filename):
        os.rename(filename, "%s.orig" % filename)
    yaml.dump(data, open(filename, "w"), default_flow_style=False)
    print "Updated %s (old version saved to %s)" % (filename,
                                                    "%s.orig" % filename)


def load(name):
    filename = "%s/%s.yaml" % (hiera_dir, name)
    return yaml.load(open(filename).read())


def update_sfconfig(data):
    dirty = False
    # 2.2.3: remove service list (useless since arch.yaml)
    if 'services' in data:
        del data['services']
        dirty = True

    # Make sure mirrors is in the conf
    if 'mirrors' not in data:
        data['mirrors'] = {
            'swift_mirror_url': 'http://swift:8080/v1/AUTH_uuid/repomirror/',
            'swift_mirror_tempurl_key': 'CHANGEME',
        }
        dirty = True
    return dirty


def clean_arch(data):
    dirty = False
    # Remove data added *IN-PLACE* by utils_refarch
    # Those are now saved in _arch.yaml instead
    for dynamic_key in ("domain", "gateway", "gateway_ip", "install",
                        "install_ip", "ip_prefix", "roles", "hosts_file"):
        if dynamic_key in data:
            del data[dynamic_key]
            dirty = True

    # Remove deployments related information
    for deploy_key in ("cpu", "disk", "mem", "hostid", "puppet_statement",
                       "rolesname", "hostname"):
        for host in data["inventory"]:
            if deploy_key in host:
                del host[deploy_key]
                dirty = True
    return dirty


if len(argv) == 2:
    hiera_dir = argv[1]
else:
    hiera_dir = "/etc/puppet/hiera/sf"

if not os.path.isdir(hiera_dir):
    print "usage: %s hiera_dir" % argv[0]
    exit(1)

# arch.yaml
try:
    arch = load("arch")
except IOError:
    # 2.1.x -> 2.2.x: arch is missing, force update
    arch = yaml.load(open(DEFAULT_ARCH).read())
    save("arch", arch)

if clean_arch(arch):
    save("arch", arch)

# sfconfig.yaml
sfconfig = load("sfconfig")
if update_sfconfig(sfconfig):
    save("sfconfig", sfconfig)
