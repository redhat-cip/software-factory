#!/bin/env python
#
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

import urllib
import json
import requests

import config
from utils import Base, skipIfServiceMissing


def get_cid_from_cookie(cookie):
    for val in urllib.unquote(cookie).split(';'):
        if val.startswith('cid='):
            return int(val.split('=')[1])
    raise RuntimeError("Couldn't find cid from cookie")


class TestStoryboard(Base):
    @skipIfServiceMissing('storyboard')
    def test_storyboard_api_access(self):
        """ Test if storyboard is accessible on gateway hosts
        """
        urls = [config.GATEWAY_URL + "/storyboard_api/projects?limit=10",
                config.GATEWAY_URL + "/storyboard_api/stories?limit=10"]

        # Unauthenticated calls
        for url in urls:
            resp = requests.get(url)
            self.assertEqual(resp.status_code, 200)

        # Authenticated calls
        cookies = dict(auth_pubtkt=config.USERS[config.USER_4]['auth_cookie'])
        headers = dict(Authorization='Bearer will-be-set-by-apache')
        for url in urls:
            resp = requests.get(url, headers=headers, cookies=cookies)
            self.assertEqual(resp.status_code, 200)

        # Bad authenticated calls
        for url in urls:
            resp = requests.get(url, headers=headers)
            self.assertEqual(resp.history[0].status_code, 307)
            self.assertIn("auth/login", resp.url)

    @skipIfServiceMissing('storyboard')
    def test_storyboard_add_story(self):
        """ Test adding a story to storyboard """
        url = "%s/storyboard_api/stories" % config.GATEWAY_URL
        story = {
            "title": "A new hope",
            "description": "A long time ago in a galaxy far, far away...",
        }

        # Unauthenticated users can't add a story
        resp = requests.post(url, data=story)
        self.assertEqual(resp.status_code, 401)

        # Test story creation
        cookies = dict(auth_pubtkt=config.USERS[config.USER_4]['auth_cookie'])
        headers = dict(Authorization='Bearer will-be-set-by-apache')
        headers['Content-Type'] = 'application/json; charset=utf8'
        resp = requests.post(url, data=json.dumps(story),
                             headers=headers, cookies=cookies)
        self.assertEqual(resp.status_code, 200)
        story_id = resp.json()['id']

        # Check story retrieval
        url = "%s/storyboard_api/stories/%d" % (config.GATEWAY_URL, story_id)
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['title'], "A new hope")

        # Check story deletion needs authenticated
        resp = requests.delete(url)
        self.assertEqual(resp.status_code, 401)
        # story deletion is admin only
        resp = requests.delete(url, headers=headers, cookies=cookies)
        self.assertEqual(resp.status_code, 403)

        cookies = dict(auth_pubtkt=config.USERS["admin"]['auth_cookie'])
        resp = requests.delete(url, headers=headers, cookies=cookies)
        self.assertEqual(resp.status_code, 204)
