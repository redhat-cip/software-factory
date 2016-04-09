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
    # 2.1.x -> 2.2.x: adds service list
    if 'services' not in data:
        data['services'] = [
            'SFRedmine',
            'SFGerrit',
            'jenkins',
            'etherpad',
            'lodgeit',
            'nodepool'
        ]
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

# sfconfig.yaml
sfconfig = load("sfconfig")
if update_sfconfig(sfconfig):
    save("sfconfig", sfconfig)
