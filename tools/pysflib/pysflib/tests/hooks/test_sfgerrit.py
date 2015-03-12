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

# We rely on https://github.com/maxtepkeev/python-redmine

from unittest import TestCase
from mock import patch, ANY

from pysflib.hooks import sfgerrit as hooks


SAMPLE_COMMIT_MSGS = [
    """This commit has no issue ID""",
    """This commit has one but not properly set: #312""",
    """This commit is cool. Bug: 354""",
    """This commit is cool too. bug: #355""",
    """This commit is okay.

Bug:            #356""",
    """This is a fix. Fix: 357""",
    """This commit has issues. Issue: 358""",
    """This commit closes a story. Story: 350""",
    """This commit is weird but should be parsed. Closes-Bug: 331""",
    """This commit does a lot.

Bug: 384
Related-to: 762""",
    """This commit is related. Related: 763""",
    """This commit is related. Related To: 764""",
    """This commit is the  ultimate fix.

Bug: 4
Bug: 8
Bug: 15
Bug: 16
Bug: 23
Bug: 42""",
]
GIT_CATFILE_ANSWER = """tree d341f9fcd9d7575d536edfbeb97cd0dbd5eb4cee
parent c077ee72b4f5a888c0df1ff97fbfb31de96cebfb
author Matthieu Huin <mhu@enovance.com> 1425897008 +0000
committer Matthieu Huin <mhu@enovance.com> 1425903247 +0000

Bump passenger version in third_party_tools
"""

hooks_conf = """
redmine_url: http://redmine.fake/
redmine_key: 1234
gitweb_url: http://gitweb.fake/"""


def fake_output_no_trigger(*args, **kwargs):
    return GIT_CATFILE_ANSWER


def fake_output_close_bug(*args, **kwargs):
    return GIT_CATFILE_ANSWER + "\nBug: #1234"


def fake_output_related_bug(*args, **kwargs):
    return GIT_CATFILE_ANSWER + "\nRelated To: #5678"


class FakeArgs:
    def __init__(self, project, commit, branch, change_url, submitter):
        self.project = project
        self.commit = commit
        self.branch = branch
        self.change_url = change_url
        self.submitter = submitter


class TestGerritHooks(TestCase):

    @classmethod
    def setupClass(cls):
        cls.hook = hooks.GerritHook(conf_file=hooks_conf)
        cls.hook.status_closing = 'Closed'
        cls.hook.status_related = 'In progress'
        cls.hook.msg = """The following change on Gerrit has been merged to: %(branch)s
Review: %(url)s
Submitter: %(submitter)s

Commit message:
%(commit)s

gitweb: %(gitweb)s
"""

    def _test_parse_commit_message(self, regexp, message, expected_result):
        self.assertEqual(expected_result,
                         hooks.parse_commit_message(message, regexp),
                         msg="Failure on message '%s'" % message)

    def test_closing_issue_regex(self):
        """test the closing issue regular expression"""
        results = [None,
                   None,
                   '354',
                   '355',
                   '356',
                   '357',
                   '358',
                   '350',
                   '331',
                   '384',
                   None,
                   None,
                   '4']
        self.assertEqual(len(results), len(SAMPLE_COMMIT_MSGS))
        for message, expected in zip(SAMPLE_COMMIT_MSGS, results):
            self._test_parse_commit_message(hooks.CLOSING_ISSUE,
                                            message,
                                            expected)

    def test_related_issue_regex(self):
        """test the related issue regular expression"""
        results = [None,
                   None,
                   None,
                   None,
                   None,
                   None,
                   None,
                   None,
                   None,
                   '762',
                   '763',
                   '764',
                   None]
        self.assertEqual(len(results), len(SAMPLE_COMMIT_MSGS))
        for message, expected in zip(SAMPLE_COMMIT_MSGS, results):
            self._test_parse_commit_message(hooks.RELATED_ISSUE,
                                            message,
                                            expected)

    def test_trimming_commit_output(self):
        with patch('subprocess.check_output',
                   new_callable=lambda: fake_output_no_trigger):
            c = self.hook.get_trimmed_commit('a1b2c3d4')
            self.assertEqual("\nBump passenger version in third_party_tools",
                             c)

    def test_main_no_trigger(self):
        args = FakeArgs('testproject',
                        '1a2b3c',
                        'master',
                        'http://change.fake',
                        'test_submitter')
        with patch('subprocess.check_output',
                   new_callable=lambda: fake_output_no_trigger):
            with patch('pysflib.sfredmine.RedmineUtils.set_issue_status') as u:
                u.return_value = True
                e = self.hook.main(args)
                self.assertEqual(0, u.call_count)
                self.assertEqual(0, e)

    def test_main_close_issue(self):
        args = FakeArgs('testproject',
                        '1a2b3c',
                        'master',
                        'http://change.fake',
                        'test_submitter')
        with patch('subprocess.check_output',
                   new_callable=lambda: fake_output_close_bug):
            with patch('pysflib.sfredmine.RedmineUtils.set_issue_status') as u:
                u.return_value = True
                e = self.hook.main(args)
                self.assertEqual(1, u.call_count)
                u.assert_called_with('1234', self.hook.status_closing,
                                     message=ANY)
                self.assertEqual(0, e)
            with patch('pysflib.sfredmine.RedmineUtils.set_issue_status') as u:
                u.return_value = False
                e = self.hook.main(args)
                self.assertEqual(1, u.call_count)
                u.assert_called_with('1234', self.hook.status_closing,
                                     message=ANY)
                self.assertEqual(1, e)

    def test_main_related_issue(self):
        args = FakeArgs('testproject',
                        '1a2b3c',
                        'master',
                        'http://change.fake',
                        'test_submitter')
        with patch('subprocess.check_output',
                   new_callable=lambda: fake_output_related_bug):
            with patch('pysflib.sfredmine.RedmineUtils.set_issue_status') as u:
                u.return_value = True
                e = self.hook.main(args)
                self.assertEqual(1, u.call_count)
                u.assert_called_with('5678', self.hook.status_related,
                                     message=ANY)
                self.assertEqual(0, e)
            with patch('pysflib.sfredmine.RedmineUtils.set_issue_status') as u:
                u.return_value = False
                e = self.hook.main(args)
                self.assertEqual(1, u.call_count)
                u.assert_called_with('5678', self.hook.status_related,
                                     message=ANY)
                self.assertEqual(1, e)
