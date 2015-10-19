#!/usr/bin/python

from sys import argv
import yaml

try:
    d = yaml.load(open(argv[1]))
except:
    print "usage: %s sfconfig.yaml" % argv[0]
    raise

# Adds default values and validation here

# Remove admin_name config option (2.0.1 -> 2.0.2)
if "admin_name" in d["authentication"]:
    if d["authentication"]["admin_name"] != "admin":
        print "Change admin name to 'admin'"
        exit(1)
    del d["authentication"]["admin_name"]

# Remove public_ip setting of nodepool (2.0.1 -> 2.0.2)
if 'public_ip' in d['nodepool']:
    del d['nodepool']['public_ip']

yaml.dump(d, open(argv[1], "w"), default_flow_style=False)
exit(0)
