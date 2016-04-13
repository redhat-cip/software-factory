#!/bin/env python
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
from utils import Base
from utils import ManageSfUtils
from utils import skipIfIssueTrackerMissing
from pysflib.sfgerrit import GerritUtils

from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError

import requests


class TestGateway(Base):
    def _auth_required(self, url):
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(resp.status_code, 307)
        self.assertTrue("/auth/login" in resp.headers['Location'])

    @skipIfIssueTrackerMissing()
    def test_redmine_root_url_for_404(self):
        """ Test if redmine yield RoutingError
        """
        url = "%s/redmine/" % config.GATEWAY_URL
        for i in xrange(11):
            resp = requests.get(url)
            self.assertNotEquals(resp.status_code, 404)

    def _url_is_not_world_readable(self, url):
        """Utility function to make sure a url is not accessible"""
        resp = requests.get(url)
        self.assertTrue(resp.status_code > 399, resp.status_code)

    def test_managesf_is_secure(self):
        """Test if managesf config.py file is not world readable"""
        url = "%s/managesf/config.py" % config.GATEWAY_URL
        self._url_is_not_world_readable(url)

    def test_cauth_is_secure(self):
        """Test if managesf config.py file is not world readable"""
        url = "%s/cauth/config.py" % config.GATEWAY_URL
        self._url_is_not_world_readable(url)

    @skipIfIssueTrackerMissing()
    # TODO(XXX) this is not up to date and can change with config
    def test_topmenu_links_shown(self):
        """ Test if all service links are shown in topmenu
        """
        subpaths = ["/r/", "/jenkins/", "/redmine/",
                    "/zuul/", "/etherpad/", "/paste/", "/docs/"]
        url = config.GATEWAY_URL + "/topmenu.html"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        for subpath in subpaths:
            self.assertTrue(('href="%s"' % subpath) in resp.text)

    def test_gerrit_accessible(self):
        """ Test if Gerrit is accessible on gateway hosts
        """
        # Unauthenticated calls
        urls = [config.GATEWAY_URL + "/r/",
                config.GATEWAY_URL + "/r/#/"]

        for url in urls:
            resp = requests.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue('<title>Gerrit Code Review</title>' in resp.text)

        # URL that requires login - shows login page
        url = config.GATEWAY_URL + "/r/a/projects/?"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('form-signin' in resp.text)

        # Authenticated URL that requires login
        url = config.GATEWAY_URL + "/r/a/projects/?"
        self._auth_required(url)
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        # /r/a/projects returns JSON list of projects
        self.assertTrue('All-Users' in resp.text)

    def test_gerrit_api_accessible(self):
        """ Test if Gerrit API is accessible on gateway hosts
        """
        m = ManageSfUtils(config.GATEWAY_URL)
        url = config.GATEWAY_URL + "/api/"

        a = GerritUtils(url)
        a.g.url = "%s/" % a.g.url.rstrip('a/')
        self.assertRaises(HTTPError, a.get_account, config.USER_1)

        api_passwd = m.create_gerrit_api_password(config.USER_1)
        auth = HTTPBasicAuth(config.USER_1, api_passwd)
        a = GerritUtils(url, auth=auth)
        self.assertTrue(a.get_account(config.USER_1))

        m.delete_gerrit_api_password(config.USER_1)
        a = GerritUtils(url, auth=auth)
        self.assertRaises(HTTPError, a.get_account, config.USER_1)

        a = GerritUtils(url)
        a.g.url = "%s/" % a.g.url.rstrip('a/')
        self.assertRaises(HTTPError, a.get_account, 'john')

    def test_jenkins_accessible(self):
        """ Test if Jenkins is accessible on gateway host
        """
        url = config.GATEWAY_URL + "/jenkins/"

        # Without SSO cookie. Note that auth is no longer enforced

        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Dashboard [Jenkins]</title>' in resp.text)

        # With SSO cookie
        resp = requests.get(
            url, cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Dashboard [Jenkins]</title>' in resp.text)

        # User should be known in Jenkins if logged in with SSO
        self.assertTrue(config.USER_1 in resp.text)

    def test_zuul_accessible(self):
        """ Test if Zuul is accessible on gateway host
        """
        url = config.GATEWAY_URL + "/zuul/"
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Zuul Status</title>' in resp.text)

    @skipIfIssueTrackerMissing()
    def test_redmine_accessible(self):
        """ Test if Redmine is accessible on gateway host
        """
        url = config.GATEWAY_URL + "/redmine/"

        # Without SSO cookie. Note that auth is no longer enforced
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Redmine</title>' in resp.text)

        # With SSO cookie
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>Redmine</title>' in resp.text)

        # User should be known in Redmine if logged in with SSO
        self.assertTrue(config.USER_1 in resp.text)

        # Check one of the CSS files to ensure static files are accessible
        css_file = "plugin_assets/redmine_backlogs/stylesheets/global.css"
        url = config.GATEWAY_URL + "/redmine/%s" % css_file
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('GLOBAL' in resp.text)

    def test_etherpad_accessible(self):
        """ Test if Etherpad is accessible on gateway host
        """
        url = config.GATEWAY_URL + "/etherpad/"
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>SF - Etherpad</title>' in resp.text)

    def test_paste_accessible(self):
        """ Test if Paste is accessible on gateway host
        """
        url = config.GATEWAY_URL + "/paste/"
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<title>New Paste | LodgeIt!</title>' in resp.text)

    def test_css_js_for_topmenu_accessible(self):
        """ Test if css/js for topmenu are accessible on gateway host
        """
        url = config.GATEWAY_URL + "/static/js/jquery.min.js"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("jQuery v2.1.1" in resp.content)

        paths = ('js/bootstrap.min.js', 'css/bootstrap.min.css')
        for p in paths:
            url = config.GATEWAY_URL + "/static/bootstrap/%s" % p
            resp = requests.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue("Bootstrap v3.2.0" in resp.content)

    def test_static_dir_for_paste_accessible(self):
        """ Test if static dir for paste is accessible on gateway host
        """
        url = config.GATEWAY_URL + "/static/lodgeit/jquery.js"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("jQuery 1.2.6" in resp.content)

    def test_docs_accessible(self):
        """ Test if Sphinx docs are accessible on gateway host
        """
        url = config.GATEWAY_URL + "/docs/index.html"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_accessible(self):
        """ Test if Dashboard is accessible on gateway host
        """
        url = config.GATEWAY_URL + "/dashboard/"

        self._auth_required(url)

        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<body ng-controller="mainController">' in resp.text)

    def test_jenkinslogs_accessible(self):
        """ Test if Jenkins logs are accessible on gateway host
        """
        url = "http://%s/jenkinslogs/127.0.0.1/dashboard/" % (
            config.GATEWAY_HOST)
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(resp.status_code, 307)

        self._auth_required(url)

        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 200)

        url = "http://%s/jenkinslogs/127.0.0.2/dashboard/" % (
            config.GATEWAY_HOST)
        resp = requests.get(
            url,
            cookies=dict(
                auth_pubtkt=config.USERS[config.USER_1]['auth_cookie']))
        self.assertEqual(resp.status_code, 404)
