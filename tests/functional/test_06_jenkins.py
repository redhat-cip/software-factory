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

from utils import Base
from utils import JenkinsUtils


class TestJenkinsBasic(Base):
    """ Functional tests to validate config repo bootstrap
    """

    def setUp(self):
        self.ju = JenkinsUtils()

    def test_config_jobs_exist(self):
        """ Test if jenkins config-update and config-check are created
        """
        url = '%s/job/config-check/' % self.ju.server
        resp = self.ju.get(url)
        self.assertEquals(resp.status_code, 200)
        url = '%s/job/config-update/' % self.ju.server
        resp = self.ju.get(url)
        self.assertEquals(resp.status_code, 200)
