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

from managesf import templates
from pecan import abort, request, conf
from cookielib import CookieJar
from subprocess import Popen, PIPE
from pwd import getpwnam
from grp import getgrnam
import os
import requests as http
import logging

logger = logging.getLogger(__name__)


def auth_cookie_in_jar(jar):
    for cookie in jar:
        if cookie.name == 'auth_pubtkt':
            return {cookie.name: cookie.value}

    return None


def admin_auth_cookie():
    if not conf.admin['cookiejar']:
        conf.admin['cookiejar'] = CookieJar()

    jar = conf.admin['cookiejar']
    cookie = auth_cookie_in_jar(jar)
    if not cookie:
        url = "http://%(auth_host)s/auth/login" % \
            {'auth_host': conf.auth['host']}
        r = http.post(url, params={'username': conf.admin['name'],
                                   'password': conf.admin['http_password'],
                                   'back': '/'},
                      allow_redirects=False)
        for c in r.cookies:
            if c.name == 'auth_pubtkt':
                cookie = {c.name: c.value}
            jar.set_cookie(c)

    return cookie


def send_request(url, expect_return,
                 method='PUT',
                 **kwargs):
    meth = http.put
    if method == 'GET':
        meth = http.get
    elif method == 'DELETE':
        meth = http.delete
    elif method == 'POST':
        meth = http.post

    if 'cookies' not in kwargs and \
       request.cookies and 'auth_pubtkt' in request.cookies.keys():
        kwargs['cookies'] = dict(auth_pubtkt=request.cookies['auth_pubtkt'])

    resp = meth(url, allow_redirects=False, **kwargs)

    if resp.status_code not in expect_return:
        logger.debug("    Request " + method + " " + url +
                     " failed with status code " +
                     str(resp.status_code) + " - " + resp.text)

        abort(resp.status_code)

    return resp


def template(t):
    return templates.__path__[0] + '/' + t


def chown(path, user, group):
    uid = getpwnam(group).pw_uid
    gid = getgrnam(user).gr_gid
    os.chown(path, uid, gid)


class RemoteUser(object):
    def __init__(self, user, host, sshkey_path=None):
        self.opt = ['-o', 'LogLevel=ERROR', '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null']
        if sshkey_path:
            self.opt = self.opt + ['-i', sshkey_path]
        self.host = '%s@%s' % (user, host)

    def _exe(self, cmd):
        logger.debug(cmd)
        p = Popen(cmd, stdout=PIPE)
        p.wait()
        return p.communicate()

    def _ssh(self, cmd):
        cmd = ['ssh'] + self.opt + [self.host] + cmd.split()
        return self._exe(cmd)

    def _scpFromRemote(self, src, dest):
        src = '%s:%s' % (self.host, src)
        cmd = ['scp'] + self.opt + [src, dest]
        return self._exe(cmd)

    def _scpToRemote(self, src, dest):
        dest = '%s:%s' % (self.host, dest)
        cmd = ['scp'] + self.opt + [src, dest]
        return self._exe(cmd)
