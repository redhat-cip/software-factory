#!/usr/bin/env python

# Copyright 2013 OpenStack Foundation
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

# borrowed from openstack-infra/system-config/tools/hieraedit.py
# to be replaced by a packaged version...

import argparse
import os
import yaml
import tempfile


# from:
# http://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data # flake8: noqa
def should_use_block(value):
    for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False


def my_represent_scalar(self, tag, value, style=None):
    if style is None:
        if should_use_block(value):
            style = '|'
        else:
            style = self.default_style

    node = yaml.representer.ScalarNode(tag, value, style=style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    return node

yaml.representer.BaseRepresenter.represent_scalar = my_represent_scalar


# end from
# from: http://pyyaml.org/ticket/64
class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
# end from

parser = argparse.ArgumentParser(description='Edit hiera yaml.')
parser.add_argument('--yaml', help='the path to the hira yaml file',
                    default='/etc/puppet/hieradata/production/common.yaml')
parser.add_argument('--eval', action='store_const', const=True,
                    help='Eval the key value before store')
parser.add_argument('--append', action='store_const', const=True,
                    help='Append value to key list instead of replace')
parser.add_argument('--delete', dest='subkey',
                    help='Delete nested dict from list if subkey match'
                         ' the value')
parser.add_argument('key', help='the key')
parser.add_argument('value', help='the value', nargs='?')
parser.add_argument('-f', dest='file', help='file to read in as value')

args = parser.parse_args()
if os.path.isfile(args.yaml):
    data = yaml.load(open(args.yaml))
else:
    data = {}
if data is None:
    data = {}

# Try to convert key to int
try:
    args.key = int(args.key)
except ValueError:
    pass

changed = False
if args.value:
    if args.eval:
        value = eval(args.value)
    else:
        value = args.value
    if args.subkey:
        new = []
        for elm in data[args.key]:
            if isinstance(elm, dict):
                if elm[args.subkey] == args.value:
                    continue
            new.append(elm)
        data[args.key] = new
    elif args.append:
        if isinstance(args.key, int):
            data.append(value)
        else:
            data[args.key].append(value)
    else:
        data[args.key] = value
    changed = True
if args.file:
    data[args.key] = open(args.file).read()
    changed = True
# print data[args.key]

if changed:
    dn = os.path.dirname(args.yaml)
    (out, fn) = tempfile.mkstemp(dir=dn)
    os.write(out, yaml.dump(data, default_flow_style=False, Dumper=MyDumper))
    os.close(out)
    os.rename(fn, args.yaml)
