#!/usr/bin/env python
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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
import tempfile
from unittest import TestCase

from sfmigration.common import utils


class TestUtils(TestCase):
    @classmethod
    def setupClass(cls):
        conf_file = tempfile.NamedTemporaryFile(delete=False)
        conf_file.write("""
[SECTION1]
this = that
#field1 = value1

[MAPPINGS]
user1 = stan
user2 = kyle
#user3 = kenny
""")
        cls.conf_file = conf_file.name
        conf_file.close()

    @classmethod
    def teardownClass(cls):
        try:
            os.unlink(cls.conf_file)
        except OSError:
            # nothing to do here
            pass

    def test_get_config_value(self):
        self.assertEqual('that',
                         utils.get_config_value(self.conf_file,
                                                'SECTION1',
                                                'this'))
        self.assertEqual(None,
                         utils.get_config_value(self.conf_file,
                                                'SECTION1',
                                                'that'))

    def test_get_mapping(self):
        self.assertEqual('stan',
                         utils.get_mapping(self.conf_file,
                                           'user1'))
        self.assertEqual('user3',
                         utils.get_mapping(self.conf_file,
                                           'user3'))
