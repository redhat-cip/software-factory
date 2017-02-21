#!/usr/bin/env python
# Copyright (C) 2016 Red Hat
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

import os
import sys
import stat
import shutil
import argparse
import tempfile
from pwd import getpwnam
from datetime import datetime
from paramiko import SSHConfig

import unittest

OWNER = 'gerrit'
SSH_CONFIG = '/var/lib/gerrit/.ssh/config'
KEYS_DB = '/var/lib/gerrit/.ssh/'

# This helper will let you modify or add (if not exists yet)
# an Alias section into /var/lib/gerrit/.ssh/config. The
# deletion is supported too. This tool will only allow you
# to add a predefined section (see the template below)
# If you need a more thourough configuration you can edit
# ssh_config after the run of that tool.

# Scenario:
# I have created a key pair for the replication of a GIT repository
# on Github. The public key has been installed as a deploy key
# on Github and I need to make sure that Gerrit will use the private key
# to authenticate on github. This script can be used to ease the
# installation of that key on Gerrit (inside its own ssh_config file)

# cat myreplkey.key | ssh root@mysfnode gerrit_repl_alias_helper --hostname \
# server.domain.com --key-from-stdin server-alias
# or (if the key has been already scp to the SF node)
# gerrit_repl_alias_helper --hostname server.domain.com --key-path \
# /tmp/myreplkey.key server-alias


section_template = {
    'host': None,
    'config': {
        'identityfile': None,
        'preferredauthentications': 'publickey',
        'hostname': None
    }
}

# Paramiko SSHConfig lowers option' names. Capitalize
# them before rewriting the file.
# Here only options supported by the Gerrit replication plugin are
# managed.
capitalize = {
    "identityfile": "IdentityFile",
    "preferredauthentications": "PreferredAuthentications",
    "hostname": "Hostname",
    "user": "User",
    "port": "Port",
    "stricthostkeychecking": "StrictHostKeyChecking",
}


def write(ssh_config):
    now = datetime.now()
    # Be safe and create a backup
    backup = os.path.join(os.path.dirname(SSH_CONFIG),
                          ".%s-%s" % (os.path.basename(SSH_CONFIG),
                                      now.strftime('%y-%m-%d_%H-%M-%S')))
    shutil.copy2(SSH_CONFIG, backup)
    print "[+] save a copy of the ssh_config file (%s)" % backup
    f = file(SSH_CONFIG, 'w')
    for host in ssh_config:
        if '*' not in host['host']:
            f.write('Host "%s"\n' % host['host'][0])
            for k, v in host['config'].items():
                if isinstance(v, list):
                    for _v in v:
                        f.write('%s %s\n' % (capitalize.get(k, k), _v))
                else:
                    f.write('%s %s\n' % (capitalize.get(k, k), v))
        f.write('\n')


def copy_key(path):
    uid = getpwnam(OWNER).pw_uid
    gid = getpwnam(OWNER).pw_gid
    if os.path.dirname(path).strip() != KEYS_DB:
        tpath = os.path.join(KEYS_DB, os.path.basename(path))
        print "[+] move %s to %s" % (path, tpath)
        shutil.copy2(path, tpath)
    else:
        # Key already in the keys db
        tpath = path
    print "[+] set key perms (%s)" % tpath
    os.chmod(tpath, stat.S_IRUSR | stat.S_IWUSR)
    os.chown(tpath, uid, gid)
    return tpath


def main(args):
    config = SSHConfig()
    if os.path.isfile(SSH_CONFIG):
        config.parse(open(SSH_CONFIG))
    else:
        print "[+] %s does not exists. Creating an empty one." % SSH_CONFIG
        file(SSH_CONFIG, 'w').write("")

    if args.delete:
        print "[+] delete section Host %s" % args.alias
        config._config = [
            section for section in config._config if
            args.alias not in section['host']]
    else:
        if (args.hostname and args.alias and
           (args.key_path or args.key_from_stdin)):
            if args.key_from_stdin:
                print "[+] read the key from stdin ..."
                fd, key_path = tempfile.mkstemp(suffix='_%s.key' % args.alias)
                for line in sys.stdin:
                    os.write(fd, line)
                os.fsync(fd)
                key_path = copy_key(key_path)
            else:
                key_path = copy_key(args.key_path)
            print "[+] add section Host %s" % args.alias
            # Clean section with the name
            config._config = [
                section for section in config._config if
                args.alias not in section['host']]
            section = section_template
            section['host'] = [args.alias]
            section['config']['hostname'] = args.hostname
            section['config']['identityfile'] = [key_path]
            config._config.append(section)
    print "[+] write the ssh_config file"
    write(config._config)


# ## Embedded tests ###
class Tests(unittest.TestCase):

    def test_copy_key(self):
        import getpass
        import mock
        with mock.patch.dict(globals(), {'OWNER': getpass.getuser(),
                                         'KEYS_DB': tempfile.mkdtemp()}):
            key_path = tempfile.mkstemp()[1]
            name = os.path.basename(key_path)
            copy_key(key_path)
            self.assertTrue(os.path.isfile(os.path.join(KEYS_DB, name)))

    def test_write(self):
        import mock
        sshconf = section_template
        sshconf['host'] = ['test']
        sshconf['config']['hostname'] = 'test.domain.test'
        sshconf['config']['identityfile'] = ['/to/the/key']
        target_sshconf = tempfile.mkstemp()[1]
        with mock.patch.dict(globals(), {'SSH_CONFIG': target_sshconf}):
            write([sshconf])
            config = SSHConfig()
            config.parse(open(target_sshconf))
        self.assertTrue('test' in config._config[1]['host'])

    def test_main(self):
        import mock
        import copy
        sshconf1 = copy.deepcopy(section_template)
        sshconf1['host'] = ['test1']
        sshconf1['config']['hostname'] = 'test.domain.test'
        sshconf1['config']['identityfile'] = ['/to/the/key']
        sshconf2 = copy.deepcopy(section_template)
        sshconf2['host'] = ['test2']
        sshconf2['config']['hostname'] = 'test.domain.test'
        sshconf2['config']['identityfile'] = ['/to/the/key']
        target_sshconf = tempfile.mkstemp()[1]
        with mock.patch.dict(globals(), {'SSH_CONFIG': target_sshconf}):
            # Create a dummy ssh_config file
            write([sshconf1, sshconf2])

            # Call the app with delete args
            args = mock.MagicMock(delete=True, alias='test1')
            main(args)
            # Read the target file and check content
            config = SSHConfig()
            config.parse(open(target_sshconf))
            self.assertTrue("test2" in [e['host'][0] for
                            e in config._config])
            self.assertTrue("test1" not in [e['host'][0] for
                            e in config._config])

            # Call the app with a add/replace args
            args = mock.MagicMock(alias='backup', hostname='backupserver',
                                  key_path='/tmp/mykey', delete=False,
                                  key_from_stdin=False)
            with mock.patch.dict(globals(),
                                 {"copy_key":
                                  mock.Mock(return_value='/tmp/mykey')}):
                main(args)
            # Read the target file and check content
            config = SSHConfig()
            config.parse(open(target_sshconf))
            self.assertTrue("test2" in [e['host'][0] for
                            e in config._config])
            self.assertTrue("backup" in [e['host'][0] for
                            e in config._config])

# ## End of unittest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Helper for gerrit/.ssh/config')
    parser.add_argument('alias', type=str, help='Host alias name')
    parser.add_argument('--delete', action='store_true', default=False,
                        help='Delete a section')
    parser.add_argument('--hostname', type=str, help='Target host')
    parser.add_argument('--key-path', type=str,
                        help='Absolute path to the key')
    parser.add_argument('--key-from-stdin', action='store_true',
                        default=False,
                        help='Read the key from stdin')

    args = parser.parse_args()

    main(args)
