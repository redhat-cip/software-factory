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

from .base import BaseGuiTest, caption, snapshot_if_failure
from .. import config


class TestAdministratorTasks(BaseGuiTest):

    @snapshot_if_failure
    def test_create_project(self):
        self.driver.get(config.GATEWAY_URL)
        self.login_as(config.ADMIN_USER, config.ADMIN_PASSWORD)

        msg = "Log in as adminstrator Go to the dashboard from the top menu"
        with caption(self.driver, msg) as driver:
            driver.get("%s/dashboard/" % config.GATEWAY_URL)

        #TODO (gp) Give the buttons an element id
        msg = "Click on 'Create project' bottom"
        with caption(self.driver, msg) as driver:
            driver.find_element_by_css_selector("button.btn-primary").click()

        msg = "Describe your project"
        with caption(self.driver, msg) as driver:
            self.highlight("#projectname").send_keys("Demo_Project")
            self.highlight("#description").send_keys("Test Description")
            ele = self.highlight_button("Create project")
            ele.click()

        msg = "Now you have a project ready to work"
        with caption(self.driver, msg) as driver:
            self.highlight_link("Demo_Project").click()
        msg = "Thank you for watching"
        with caption(self.driver, msg) as driver:
            self.highlight("body")


if __name__ == '__main__':
    from unittest import main
    main()
