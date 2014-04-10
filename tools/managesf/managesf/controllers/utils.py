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
from pecan import abort
import requests as http


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
    resp = meth(url, **kwargs)
    if resp.status_code not in expect_return:
        print "    Request " + method + " " + url + \
              " failed with status code " + \
              str(resp.status_code) + " - " + resp.text

        abort(resp.status_code)

    return resp


def template(t):
    return templates.__path__[0] + '/' + t
