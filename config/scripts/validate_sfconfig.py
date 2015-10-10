#!/usr/bin/python

from sys import argv
import yaml

try:
    d = yaml.load(open(argv[1]))
except:
    print "usage: %s sfconfig.yaml" % argv[0]
    raise

# Adds default values and validation here


yaml.dump(d, open(argv[1], "w"), default_flow_style=False)
exit(0)
