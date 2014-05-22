#!/bin/sh

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
export SF_SUFFIX=${SF_SUFFIX:-tests.dom}
# Gerrit
socat TCP-LISTEN:80,fork TCP:gerrit.${SF_SUFFIX}:80 &
# Redmine
socat TCP-LISTEN:81,fork TCP:redmine.${SF_SUFFIX}:80 &
# Jenkins
socat TCP-LISTEN:8080,fork TCP:jenkins.${SF_SUFFIX}:8080 &
# Etherpad
socat TCP-LISTEN:82,fork TCP:commonservices.${SF_SUFFIX}:80 &
# Logdeit
socat TCP-LISTEN:83,fork TCP:commonservices.${SF_SUFFIX}:8080 &
# Zuul
socat TCP-LISTEN:84,fork TCP:jenkins.${SF_SUFFIX}:80 
