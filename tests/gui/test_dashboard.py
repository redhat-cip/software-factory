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

import unittest
from pyvirtualdisplay import Display
from selenium import webdriver
# from selenium.webdriver.common.keys import Keys

import config


class TestSoftwareFactoryDashboard(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.display = Display(visible=0, size=(1280, 800))
        self.display.start()

    def _internal_login(self, driver, user, password):
        u = driver.find_element_by_id("username")
        u.send_keys(user)
        p = driver.find_element_by_id("password")
        p.send_keys(password)
        p.submit()

    def test_admin_login(self):
        driver = self.driver
        driver.get(config.GATEWAY_URL)
        self.assertIn("SF", driver.title)
        self._internal_login(driver, config.USER_1, config.USER_1_PASSWORD)
        self.assertTrue("Project" in driver.page_source)
        self.assertTrue("Open Reviews" in driver.page_source)

    def tearDown(self):
        self.driver.quit()
        self.display.stop()
