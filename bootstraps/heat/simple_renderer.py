#!/usr/bin/env python
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import jinja2
import sys


# Read conf
def load_conf():
    params = {}
    for line in open('conf').readlines():
        if line[0] in ('#', '\n', ' '):
            continue
        line = line.replace('"', '')
        k, v = line.split('=')
        params[k] = v[:-1]
    params['sg_admin_cidr'] = params['sg_admin_cidr'].split()
    params['sg_user_cidr'] = params['sg_user_cidr'].split()
    return params

# Jinja
try:
    template = jinja2.Template(open(sys.argv[1]).read())
except IndexError:
    print "usage: %s template" % sys.argv[0]
    exit(1)

print template.render(load_conf())
