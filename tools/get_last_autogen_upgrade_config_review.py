#!/usr/bin/python

# Helper script to find the review id of the
# auto generated commit by the upgrade process

import requests
import json
import sys

search_string = sys.argv[2]

r = requests.get(
    '%s/r/changes/?q=%s' % (sys.argv[1], search_string))
lastid = 0
for r in json.loads(r.content[4:]):
    if r['_number'] > lastid:
        lastid = r['_number']
print lastid
