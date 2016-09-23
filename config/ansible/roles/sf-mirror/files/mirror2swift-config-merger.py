#!/usr/bin/python
#
# Copyright 2016 Red Hat
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

import sys
import os
import yaml

if len(sys.argv) != 3 or not os.path.exists(sys.argv[1]):
    print "usage: %s mirrors-dir output-conf.yaml" % sys.argv[0]
    exit(1)

# Collect mirrors configuration files
if os.path.isfile(sys.argv[1]):
    paths = [sys.argv[1]]
else:
    paths = []
    for root, dirs, files in os.walk(sys.argv[1], topdown=True):
        paths.extend([os.path.join(root, path) for path in files])

# Keeps only .yaml files
paths = filter(lambda x: x.endswith('.yaml') or x.endswith('.yml'), paths)

# swift2mirror configuration template
conf = {
    "sfmirrors": {
        "mirrors": [],
        "swift": {
            "url": "MIRROR2SWIFT_URL",
            "key": "MIRROR2SWIFT_TEMPURL_KEY",
            "ttl": "MIRROR2SWIFT_TTL",
        },
    }
}

# Add mirrors definition
for path in paths:
    data = yaml.load(open(path))
    if not data:
        continue
    for mirror in data:
        conf["sfmirrors"]["mirrors"].append(mirror)

open(sys.argv[2], "w").write(yaml.dump(conf, indent=4))
