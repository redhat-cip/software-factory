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

import base64
import requests as http
import json
import argparse
import sys


def split_and_strip(s):
    l = s.split(',')
    return [x.strip() for x in l]

parser = argparse.ArgumentParser(
    description="Tool to manage project creation and deletion")
parser.add_argument('--host', metavar='ip-address',
                    help='Softwarefactory public IP address', required=True)
parser.add_argument('--port', metavar='port-number',
                    help="Softwarefactory HTTP port number", default=80)
parser.add_argument('--auth', metavar='username:password',
                    help='Authentication information', required=True)
parser.add_argument('--auth-server', metavar='central-auth-server',
                    default='auth.sf.dom',
                    help='Hostname of the central auth server')
parser.add_argument('--cookie', metavar='Authentication cookie',
                    help='cookie of the user if known')

sp = parser.add_subparsers(dest="command")
bkpg = sp.add_parser('backup_get')
bkps = sp.add_parser('backup_start')
rst = sp.add_parser('restore')
rst.add_argument('--filename', '-n', nargs='?', metavar='tarball-name',
                 required=True,
                 help='Tarball used to restore SF')
cp = sp.add_parser('create')
cp.add_argument('--name', '-n', nargs='?', metavar='project-name',
                required=True)
cp.add_argument('--description', '-d', nargs='?',
                metavar='project-description')
cp.add_argument('--upstream', '-u', nargs='?',
                metavar='GIT link')
cp.add_argument('--core-group', '-c', metavar='core-group-members',
                help='member ids separated by comma', nargs='?')
cp.add_argument('--ptl-group', '-p', metavar='ptl-group-members',
                help='member ids serarated by comma', nargs='?')
cp.add_argument('--dev-group', '-e', metavar='dev-group-members',
                help='member ids serarated by comma' +
                     ' (only relevant for private project)',
                nargs='?')
cp.add_argument('--private', action='store_true',
                help='set if the project is private')

dp = sp.add_parser('delete')
dp.add_argument('--name', '-n', nargs='?', metavar='project-name',
                required=True)

trp = sp.add_parser('trigger_replication')
trp.add_argument('--wait', default=False,
                 action='store_true')
trp.add_argument('--project', metavar='project-name')
trp.add_argument('--url', metavar='repo-url')

rp = sp.add_parser('replication_config')
rps = rp.add_subparsers(dest="rep_command")

repl = rps.add_parser('list', help='List the sections and its content'
                      ' accessible to this user')

repa = rps.add_parser('add', help='Add a setting to the section with a value')
repa.add_argument('--section',  nargs='?', required=True,
                  help='section to which this setting belongs to')
repa.add_argument('name', metavar='name', nargs='?',
                  help='Setting name. Supported settings - project, url')
repa.add_argument('value',  nargs='?', help='Value of the setting')

repg = rps.add_parser('get-all',
                      help='Get all the values of a section setting')
repg.add_argument('--section',  nargs='?', required=True,
                  help='section to which this setting belongs to')
repg.add_argument('name', metavar='name', nargs='?',
                  help='Setting name. Supported settings - project, url')

repu = rps.add_parser('unset-all',
                      help='Remove the setting from the section')
repu.add_argument('--section',  nargs='?', required=True,
                  help='section to which this setting belongs to')
settings = 'projects, url, push, receivepack, uploadpack, timeout,'
settings = settings + ' replicationDelay, threads'
repu.add_argument('name', metavar='name', nargs='?',
                  help='Setting name. Supported settings - ' + settings)

repr = rps.add_parser('replace-all',
                      help='replaces all the current values with '
                      'the given value for a setting')
repr.add_argument('--section',  nargs='?', required=True,
                  help='section to which this setting belongs to')
repr.add_argument('name', metavar='name', nargs='?',
                  help='Setting name. Supported settings - project, url')
repr.add_argument('value',  nargs='?', help='Value of the setting')

reprn = rps.add_parser('rename-section',  help='Rename the section')
reprn.add_argument('--section',  nargs='?', required=True,
                   help='old section name')
reprn.add_argument('value',  nargs='?', help='new section name')

reprm = rps.add_parser('remove-section', help='Remove the section')
reprm.add_argument('--section',  nargs='?', required=True,
                   help='section to be removed')

args = parser.parse_args()

if args.command in ['delete', 'create']:
    url = "http://%(host)s:%(port)s/manage/project/%(name)s" % \
        {'host': args.host,
         'port': args.port,
         'name': args.name}
else:
    base_url = "http://%(host)s:%(port)s/manage" % \
        {'host': args.host,
         'port': args.port}


def get_cookie():
    if args.cookie is not None:
        return args.cookie
    (username, password) = args.auth.split(':')
    r = http.post('http://%s/auth/login' % args.auth_server,
                  params={'username': username,
                          'password': password,
                          'back': '/'},
                  allow_redirects=False)
    return r.cookies['auth_pubtkt']

headers = {'Authorization': 'Basic ' + base64.b64encode(args.auth)}
chunk_size = 1024
if args.command == 'backup_get':
    url = base_url + '/backup'
    resp = http.get(url, headers=headers,
                    cookies=dict(auth_pubtkt=get_cookie()))
    if resp.status_code != 200:
        print "backup_get failed with status_code " + str(resp.status_code)
        sys.exit("error")
    with open('sf_backup.tar.gz', 'wb') as fd:
        for chunk in resp.iter_content(chunk_size):
            fd.write(chunk)
elif args.command == 'backup_start':
    url = base_url + '/backup'
    resp = http.post(url, headers=headers,
                     cookies=dict(auth_pubtkt=get_cookie()))
elif args.command == 'restore':
    url = base_url + '/restore'
    filename = args.filename
    if not os.path.isfile(filename):
        print "file %s not exist" % filename
        sys.exit("error")
    files = {'file': open(filename, 'rb')}
    resp = http.post(url, headers=headers, files=files,
                     cookies=dict(auth_pubtkt=get_cookie()))
elif args.command == 'delete':

    resp = http.delete(url, headers=headers,
                       cookies=dict(auth_pubtkt=get_cookie()))
    print resp.text
    if resp.status_code >= 200 and resp.status_code < 203:
        print "Success"
elif args.command == 'replication_config':
    headers['Content-Type'] = 'application/json'
    settings = ['projects', 'url', 'push', 'receivepack', 'uploadpack',
                'timeout', 'replicationDelay', 'threads']
    url = '%s/replication' % base_url
    data = {}
    if args.rep_command != "list":
        if getattr(args, 'section'):
            url = url + '/%s' % args.section
        else:
            sys.exit(0)
    if args.rep_command not in {'list', 'rename-section', 'remove-section'}:
        if getattr(args, 'name'):
            if args.name not in settings:
                print "Invalid setting %s" % args.name
                print "Valid settings are " + " , ".join(settings)
                sys.exit(0)
            url = url + '/%s' % args.name
        else:
            sys.exit(0)
    if args.rep_command in {'add', 'replace-all', 'rename-section'}:
        if getattr(args, 'value'):
            data = {'value': args.value}
        else:
            sys.exit(0)

    if args.rep_command in {'add', 'rename-section'}:
        meth = http.put
    elif args.rep_command in {'unset-all', 'replace-all', 'remove-section'}:
        meth = http.delete
    elif args.rep_command in {'get-all', 'list'}:
        meth = http.get
    resp = meth(url, headers=headers, data=json.dumps(data),
                cookies=dict(auth_pubtkt=get_cookie()))
    if args.rep_command == 'replace-all':
        resp = http.put(url, headers=headers, data=json.dumps(data),
                        cookies=dict(auth_pubtkt=get_cookie()))
    # These commands need json as output,
    # if server has no valid json it will send {}
    # for other commands print status
    if args.rep_command in {'get-all', 'list'}:
        print resp.json()
    elif resp.status_code >= 200 and resp.status_code < 203:
        print "Success"

elif args.command == 'trigger_replication':
    headers['Content-Type'] = 'application/json'
    url = '%s/replication' % base_url
    info = {}
    if args.wait:
        info['wait'] = 'true'
    else:
        info['wait'] = 'false'
    if getattr(args, 'url'):
        info['url'] = args.url
    if getattr(args, 'project'):
        info['project'] = args.project
    resp = http.post(url, headers=headers, data=json.dumps(info),
                     cookies=dict(auth_pubtkt=get_cookie()))
    print resp.text
    if resp.status_code >= 200 and resp.status_code < 203:
        print "Success"
elif args.command == 'create':
    if getattr(args, 'core_group'):
        args.core_group = split_and_strip(args.core_group)
    if getattr(args, 'ptl_group'):
        args.ptl_group = split_and_strip(args.ptl_group)
    if getattr(args, 'dev_group'):
        args.dev_group = split_and_strip(args.dev_group)
    substitute = {'description': 'description',
                  'core_group': 'core-group-members',
                  'ptl_group': 'ptl-group-members',
                  'dev_group': 'dev-group-members',
                  'upstream': 'upstream',
                  'private': 'private'
                  }
    info = {}
    for word in ['description', 'core_group', 'ptl_group',
                 'dev_group', 'upstream', 'private']:
        if getattr(args, word):
            info[substitute[word]] = getattr(args, word)

    data = None
    if len(info.keys()):
        data = json.dumps(info)

    resp = http.put(url, headers=headers, data=data,
                    cookies=dict(auth_pubtkt=get_cookie()))

    print resp.text
    if resp.status_code >= 200 and resp.status_code < 203:
        print "Success"
    else:
        sys.exit(1)
