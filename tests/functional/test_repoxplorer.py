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

import config
import requests

from utils import Base
from utils import skipIfServiceMissing


class TestRepoxplorer(Base):

    @skipIfServiceMissing('repoxplorer')
    def test_repoxplorer_accessible(self):
        """ Test if RepoXplorer is accessible on gateway hosts
        """
        url = config.GATEWAY_URL + "/repoxplorer/"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('[RepoXplorer] - Projects listing' in resp.text)

    @skipIfServiceMissing('repoxplorer')
    def test_repoxplorer_data_indexed(self):
        """ Test if RepoXplorer has indexed the config repository
        """
        url = config.GATEWAY_URL + "/repoxplorer/commits.json?pid=internal"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()[2] > 0)

    @skipIfServiceMissing('repoxplorer')
    def test_repoxplorer_displayed_top_menu(self):
        """ Test if RepoXplorer link is displayed in the top menu
        """
        url = config.GATEWAY_URL + "/topmenu.html"
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('href="/repoxplorer/"' in resp.text,
                        'repoxplorer not present as a link')
