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

import os
import config

from utils import Base
from utils import GerritGitUtils

from pysflib.sfgerrit import GerritUtils


class TestConfigRepo(Base):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_check_config_repo_exists(self):
        """ Validate config repo has been bootstraped
        """
        pname = 'config'
        gu = GerritUtils(
            config.GATEWAY_URL,
            auth_cookie=config.USERS[config.ADMIN_USER]['auth_cookie'])
        self.assertTrue(gu.project_exists(pname))

        ggu = GerritGitUtils(config.ADMIN_USER,
                             config.ADMIN_PRIV_KEY_PATH,
                             config.USERS[config.ADMIN_USER]['email'])
        url = "ssh://%s@%s:29418/%s" % (config.ADMIN_USER,
                                        config.GATEWAY_HOST, pname)
        clone_dir = ggu.clone(url, pname)
        # Test that the clone is a success
        self.assertTrue(os.path.isdir(clone_dir))
        # Check if the clone dir has projects file
        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    "jobs/projects.yaml")))

        self.assertTrue(os.path.isfile(os.path.join(clone_dir,
                                                    "policies/policy.yaml")))
