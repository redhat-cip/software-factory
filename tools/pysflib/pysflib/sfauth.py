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

import requests


def get_cookie(auth_server,
               username=None, password=None,
               github_access_token=None,
               use_ssl=False, verify=True):
    if username and password:
        url = "%s/auth/login" % auth_server
        params = {'username': username,
                  'password': password,
                  'back': '/'}
    elif github_access_token:
        url = "%s/auth/login/githubAPIkey/" % auth_server
        params = {'token': github_access_token,
                  'back': '/'}
    else:
        raise ValueError("Missing credentials")
    if use_ssl:
        url = "https://" + url
        resp = requests.post(url, params, allow_redirects=False,
                             verify=verify)
    else:
        url = "http://" + url
        resp = requests.post(url, params, allow_redirects=False)
    return resp.cookies.get('auth_pubtkt', '')
