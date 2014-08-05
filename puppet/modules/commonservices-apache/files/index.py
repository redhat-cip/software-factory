#!/usr/bin/python

import os

from string import Template

print "Content-Type: text/html"
print

tmpl = Template(file('index.html.tmpl').read())
target = os.environ['REQUEST_URI']
if target.startswith('/_'):
    target = '/' + target[2:]
else:
    target = '/r/'
content = tmpl.substitute(target_url=target)
print content
