#!/usr/bin/python

import os
from urllib import unquote

from string import Template

print "Content-Type: text/html"
print

tmpl = Template(file('index.html.tmpl').read())
target = os.environ['REQUEST_URI']
if target.startswith('/_'):
    target = '/' + target.lstrip('/').lstrip('_')
    target = unquote(target)
    target = target.replace('|', '#', 1)
else:
    target = '/dashboard/'
content = tmpl.substitute(target_url=target)
print content
