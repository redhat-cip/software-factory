#!/usr/bin/python
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

import config
import unittest

import requests


class TestGateway(unittest.TestCase):
    def test_topmenu_links_shown(self):
        """ Test if all service links are shown in topmenu
        """
        subpaths = ["/r/", "/jenkins/", "/redmine/",
                    "/zuul/", "/etherpad/", "/paste/", "/docs/"]
        url = "http://%s/" % config.GATEWAY_HOST
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        for subpath in subpaths:
            self.assertTrue(('href="%s"' % subpath) in resp.text)

    def test_gerrit_accessible(self):
        """ Test if Gerrit is accessible on gateway hosts
        """
        url = "http://%s/r/" % config.GATEWAY_HOST
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Gerrit Code Review</title>' in resp.text)

    def test_jenkins_accessible(self):
        """ Test if Jenkins is accessible on gateway host
        """
        url = "http://%s/jenkins/" % config.GATEWAY_HOST
        resp = requests.get(
            url, cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Dashboard [Jenkins]</title>' in resp.text)

    def test_zuul_accessible(self):
        """ Test if Zuul is accessible on gateway host
        """
        url = "http://%s/zuul/" % config.GATEWAY_HOST
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Zuul Status</title>' in resp.text)

    def test_redmine_accessible(self):
        """ Test if Redmine is accessible on gateway host
        """
        url = "http://%s/redmine/" % config.GATEWAY_HOST
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Redmine</title>' in resp.text)

        # Check one of the CSS files to ensure static files are accessible
        css_file = "plugin_assets/redmine_backlogs/stylesheets/global.css"
        url = "http://%s/redmine/%s" % (config.GATEWAY_HOST, css_file)
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('GLOBAL' in resp.text)

    def test_etherpad_accessible(self):
        """ Test if Etherpad is accessible on gateway host
        """
        url = "http://%s/etherpad/" % config.GATEWAY_HOST
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>SF - Etherpad</title>' in resp.text)

    def test_paste_accessible(self):
        """ Test if Paste is accessible on gateway host
        """
        url = "http://%s/paste/" % config.GATEWAY_HOST
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>New Paste | LodgeIt!</title>' in resp.text)

    def test_css_js_for_topmenu_accessible(self):
        """ Test if css/js for topmenu are accessible on gateway host
        """
        url = "http://%s/static/js/jquery.min.js" % config.GATEWAY_HOST
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("jQuery v2.1.1" in resp.content)

        paths = ('js/bootstrap.min.js', 'css/bootstrap.min.css')
        for p in paths:
            url = "http://%s/static/bootstrap/%s" % (config.GATEWAY_HOST, p)
            resp = requests.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue("Bootstrap v3.2.0" in resp.content)

    def test_static_dir_for_paste_accessible(self):
        """ Test if static dir for paste is accessible on gateway host
        """
        url = "http://%s/static/lodgeit/jquery.js" % config.GATEWAY_HOST
        resp = requests.get(url)
        print url, resp.content  # for debugging gate only
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("jQuery 1.2.6" in resp.content)

    def test_docs_accessible(self):
        """ Test if Sphinx docs are accessible on gateway host
        """
        url = "http://%s/docs/index.html" % config.GATEWAY_HOST
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
