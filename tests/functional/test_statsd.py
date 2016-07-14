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

import requests
import config
from utils import Base, skipIfServiceMissing


class TestStatsd(Base):
    @skipIfServiceMissing('statsd')
    def test_zuul_metrics(self):
        # Check if Zuul metrics are received by Gnocchi and displayed in
        # Grafana
        resp = requests.get(
            'http://%s/grafana/api/dashboards/db/zuul' % config.GATEWAY_HOST)
        self.assertTrue('zuul.pipeline' in resp.text)
        self.assertTrue('gerrit.event' in resp.text)
