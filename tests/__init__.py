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

import subprocess
import os


def setUpPackage():
    if "SF_SKIP_BOOTSTRAP" in os.environ:
        return
    os.chdir("lxc")
    if "SF_PREFIX" not in os.environ or os.environ["SF_PREFIX"] == "sf":
        # Make sure we use a tests prefix
        os.environ["SF_PREFIX"] = "tests"
    subprocess.call(['./bootstrap-lxc.sh'])
    os.chdir("..")


def tearDownPackage():
    if "SF_SKIP_BOOTSTRAP" in os.environ:
        return
    os.chdir("lxc")
    subprocess.call(['./bootstrap-lxc.sh', 'stop'])
    os.chdir("..")
