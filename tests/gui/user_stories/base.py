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

from contextlib import contextmanager
import functools
import os
import time
import unittest

from selenium import webdriver


BOOTSTRAP_CAPTION = '''
ele = document.createElement("div");
ele.id = "caption-box";
ele.style.cssText = "color: #3c763d; background-color: #dff0d8;" +
" border-color: #d6e9c6; position: fixed; left: 0; top: 90%; z-index: 9999;" +
" width: 100%; height: 60px; padding: 15px; margin-bottom: 20px;";
ele.innerText = arguments[0];
body = document.getElementsByTagName("body")[0];
body.appendChild(ele);
'''


def snapshot_if_failure(func):
    @functools.wraps(func)
    def f(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            path = '/tmp/gui/'
            if not os.path.isdir(path):
                os.makedirs(path)
            screenshot = os.path.join(path, '%s.png' % func.__name__)
            self.driver.save_screenshot(screenshot)
            raise e
    return f


@contextmanager
def caption(driver, message, duration=3):
    yield driver
    driver.execute_script(BOOTSTRAP_CAPTION, message)
    time.sleep(duration)


class BaseGuiTest(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.maximize_window()

    def tearDown(self):
        self.driver.quit()

    def login_as(self, username, passwd):
        iframe = self.driver.find_element_by_tag_name("iframe")
        self.driver.switch_to.frame(iframe)
        self.driver.find_element_by_id("login-btn").click()
        self.driver.switch_to.default_content()
        self.driver.find_element_by_name("username").send_keys(username)
        self.driver.find_element_by_name("password").send_keys(passwd)
        self.driver.find_element_by_name("password").submit()

    def _highlight_element(self, element):
        style = element.get_attribute('style')
        hightlight = "%s background: yellow; border: 2px solid red;" % style
        js = "arguments[0].setAttribute('style', arguments[1]);"
        self.driver.execute_script(js, element, hightlight)
        time.sleep(.3)
        self.driver.execute_script(js, element, style)
        return element

    def highlight(self, css_selector):
        element = self.driver.find_element_by_css_selector(css_selector)
        return self._highlight_element(element)

    def highlight_link(self, link_text):
        element = self.driver.find_element_by_link_text(link_text)
        return self._highlight_element(element)

    def highlight_button(self, btn_text):
        xpath = '//button[text()="%s"]' % btn_text
        element = self.driver.find_element_by_xpath(xpath)
        return self._highlight_element(element)
