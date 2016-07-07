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
# -*- coding: utf-8 -*-

import codecs
import json
import os
import subprocess
from unittest import skipIf

try:
    import spielbash
except ImportError:
    spielbash = None

from tests.gui.base import BaseGuiTest, caption, snapshot_if_failure
from tests.gui.base import loading_please_wait
from tests.functional import config


ENV = os.environ
ENV['LANG'] = 'en_US.UTF-8'
ENV['LC_CTYPE'] = ENV['LANG']
ENV['PATH'] = '/bin:/usr/bin:/usr/local/bin'


writer = codecs.getwriter('utf8')


class MockMovie:
    def __init__(self, *args, **kwargs):
        self.vars = {}

    def flush_vars(self):
        self.vars = {}


class ShellRecorder(BaseGuiTest):

    def make_reel(self, session_name):
        reel = subprocess.Popen('tmux new-session -d -s %s' % session_name,
                                stdout=writer(subprocess.PIPE),
                                stderr=subprocess.PIPE,
                                shell=True, env=ENV)
        return reel

    def start_movie(self, session_name, title, output_file):
        asciinema_cmd = 'asciinema rec -c "tmux attach -t %s"' % session_name
        asciinema_cmd += ' -y -t "%s"' % title
        asciinema_cmd += ' %s' % output_file
        movie = subprocess.Popen(asciinema_cmd,
                                 stdout=writer(subprocess.PIPE),
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 env=ENV)
        return movie

    def start_display(self, session_name):
        ENV.update({'DISPLAY': ':99', })
        xterm = 'xterm -u8 -e "tmux attach -t %s"'
        display = subprocess.Popen(xterm % session_name,
                                   stdout=writer(subprocess.PIPE),
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   env=ENV)
        return display

    def record(self, session_name, title, output_file):
        reel = self.make_reel(session_name)
        display = self.start_display(session_name)
        movie = self.start_movie(session_name, title, output_file)
        return reel, display, movie

    def stop_recording(self, session_name, reel, display, movie, output_file):
        spielbash.TmuxSendKeys(session_name, 'exit')
        spielbash.TmuxSendKeys(session_name, 'C-m')
        reel.communicate('exit')
        out, err = movie.communicate()
        print out
        print err
        display.communicate()
        with open(output_file, 'r') as m:
            j = json.load(m)
        if not j.get('width'):
            j['width'] = 80
        if not j.get('height'):
            j['height'] = 25
        with open(output_file, 'w') as m:
            json.dump(j, m)

    def play_scene(self, session_name, scene, mock_movie):
        spielbash.pause(0.4)
        s = None
        if 'action' in scene:
            s = spielbash.Scene(scene['name'], scene.get('action', ''),
                                session_name,
                                scene.get('keep', {}), mock_movie,
                                wait_for_execution=scene.get('wait', False))
        elif 'line' in scene:
            s = spielbash.Dialogue(scene['line'], session_name)
        elif 'press_key' in scene:
            s = spielbash.PressKey(scene['press_key'], session_name)
        elif 'pause' in scene:
            spielbash.pause(scene.get('pause', 1))
        else:
            raise Exception('Unknown scene type %r' % scene)
        if s:
            s.run()


class TestAdministratorTasks(ShellRecorder):

    @snapshot_if_failure
    def test_create_project(self):
        self.driver.get(config.GATEWAY_URL)
        self.login_as(config.ADMIN_USER, config.ADMIN_PASSWORD)

        msg = ("Log in as administrator, "
               "then go to the dashboard from the top menu.")
        with caption(self.driver, msg) as driver:
            driver.get("%s/dashboard/" % config.GATEWAY_URL)

        #TODO (gp) Give the buttons an element id
        msg = "Click on the 'Create project' button."
        with loading_please_wait(self.driver) as driver:
            with caption(driver, msg) as _d:
                _d.find_element_by_css_selector("button.btn-primary").click()

        msg = ("Define your project here. "
               "Eventually specify an upstream repo to clone from.")
        with caption(self.driver, msg):
            self.highlight("#projectname").send_keys("Demo_Project")
            self.highlight("#description").send_keys("Test Description")
            ele = self.highlight_button("Create project")
            ele.click()

        msg = "Now your project is ready."
        with loading_please_wait(self.driver) as driver:
            with caption(driver, msg):
                self.highlight_link("Demo_Project").click()

        msg = "Thank you for watching !"
        with caption(self.driver, msg):
            self.highlight("body")

    @skipIf(spielbash is None,
            'missing spielbash dependency')
    def test_create_project_from_CLI(self):
        sfm = "sfmanager --url %s --auth-server-url %s --auth %s:%s "
        sfm = sfm % (config.GATEWAY_URL, config.GATEWAY_URL,
                     config.ADMIN_USER, config.ADMIN_PASSWORD)
        sfm += "project create --name %s" % 'CLI_project'
        scenes = [
            {'name': 'Create a project from the CLI',
             'action': sfm,
             'keep': {},
             'wait': True},
        ]
        session_name = 'create_project_from_CLI'
        r, d, m = self.record(session_name,
                              'Create a project from the CLI',
                              '/tmp/gui/create_project_from_CLI.json')
        mock_movie = MockMovie()
        for scene in scenes:
            self.play_scene(session_name, scene, mock_movie)

        self.stop_recording(session_name, r, d, m,
                            '/tmp/gui/create_project_from_CLI.json')

        self.driver.get(config.GATEWAY_URL)
        self.login_as(config.ADMIN_USER, config.ADMIN_PASSWORD)

        self.driver.get("%s/dashboard/" % config.GATEWAY_URL)
        with loading_please_wait(self.driver):
            project = self.highlight_link("CLI_project")
            spielbash.pause(0.5)
            project.click()


if __name__ == '__main__':
    from unittest import main
    main()
