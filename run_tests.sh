#!/bin/bash
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

source functestslib.sh
echo "Running unit-tests with this HEAD"
display_head

bash ./rpm-test-requirements.sh

echo "$(date) - $(hostname)"

echo "FLAKE8 tests"
echo "~~~~~~~~~~~~"
find . -iname "*.py" -o -name "change-merged" -o -name "patchset-created" | grep -v .tox | xargs flake8
FLAKE8_ERRORS=$?
echo

echo "BASH8 tests"
echo "~~~~~~~~~~~"
find . -name "*.sh" -or -name "*.install" | grep -v '\.tox' | xargs bash8
BASH8_ERRORS=$?
echo

echo "gerrit_repl_alias_helper.py tests"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
(cd config/scripts/; sudo pip install mock; nosetests -v gerrit_repl_alias_helper.py)
REPL_TOOL_ERRORS=$?
echo

exit $[${FLAKE8_ERRORS} + ${BASH8_ERRORS} + ${REPL_TOOL_ERRORS}];
