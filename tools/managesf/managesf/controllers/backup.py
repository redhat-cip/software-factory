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

from pecan import conf
from pecan import abort
import logging
from utils import RemoteUser
from gerrit import user_is_administrator


logger = logging.getLogger(__name__)


class Backup(object):
    def __init__(self):
        if not user_is_administrator():
            abort(401)
        path = conf.managesf['sshkey_priv_path']
        self.gru = RemoteUser('root', conf.gerrit['host'], path)
        self.jru = RemoteUser('root', conf.jenkins['host'], path)
        self.msqlru = RemoteUser('root', conf.mysql['host'], path)
        self.pmru = RemoteUser('root', conf.puppetmaster['host'], path)

    def start(self):
        cmd = '/root/backup.sh'
        logger.debug(" start backup of Gerrit, jenkins and mysql")
        self.gru._ssh(cmd)
        self.jru._ssh(cmd)
        self.pmru._ssh(cmd)
        self.msqlru._ssh(cmd)

    def get(self):
        self.msqlru._scpFromRemote('/root/sf_backup.tar.gz',
                                   '/tmp/sf_backup.tar.gz')

    def restore(self):
        self.msqlru._scpToRemote('/tmp/sf_backup.tar.gz',
                                 '/root/sf_backup.tar.gz')
        cmd = '/root/restore.sh'
        self.msqlru._ssh(cmd)
        self.gru._ssh(cmd)
        self.jru._ssh(cmd)
        self.pmru._ssh(cmd)


def backup_start():
    bkp = Backup()
    bkp.start()


def backup_get():
    bkp = Backup()
    bkp.get()


def backup_restore():
    bkp = Backup()
    bkp.restore()
