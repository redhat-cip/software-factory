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
import os
import requests
import yaml

from utils import Base


class TestJenkinsBasic(Base):
    """ Functional tests to validate config repo bootstrap
    """

    def setUp(self):
        """ Tests is executed on puppetmaster, so read config from Hiera file
        and get credentials for the Jenkins user """
        fh = open('/etc/puppet/hiera/sf/jenkins.yaml')
        config = yaml.load(fh)
        self.jenkins_password = config.get('jenkins').get('jenkins_password')
        fh.close()

    def test_config_jobs_exist(self):
        """ Test if jenkins config-update and config-check are created
        """
        url = '%s/job/config-check' % config.JENKINS_SERVER
        resp = requests.get(url, auth=('jenkins', self.jenkins_password))
        self.assertEquals(resp.status_code, 200)
        url = '%s/job/config-update' % config.JENKINS_SERVER
        resp = requests.get(url, auth=('jenkins', self.jenkins_password))
        self.assertEquals(resp.status_code, 200)
