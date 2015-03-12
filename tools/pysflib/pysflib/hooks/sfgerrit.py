#!/usr/bin/env python
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


"""Library of utilities for the gerrit hooks."""


import argparse
import logging
from logging.handlers import RotatingFileHandler
import re
import subprocess
import yaml

from six.moves import urllib_parse

from pysflib.sfredmine import RedmineUtils


# Common patterns used in our hooks
CLOSING_ISSUE_REGEX = """(
[Bb]ug|
[Ff]ix|
[Ss]tory|
[Ii]ssue|
[Cc]loses?)
:\s+
\#?(\d+)"""
CLOSING_ISSUE = re.compile(CLOSING_ISSUE_REGEX, re.VERBOSE)
RELATED_ISSUE_REGEX = """(
[Rr]elated|
[Rr]elated[ -][Tt]o)
:\s+
\#?(\d+)"""
RELATED_ISSUE = re.compile(RELATED_ISSUE_REGEX, re.VERBOSE)


DEFAULT_CLI_OPTIONS = ('change', 'change-url', 'project',
                       'branch', 'topic', 'submitter', 'commit')


# logging
logfile = '/tmp/gerrithooks.log'  # TODO find a better place for this
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_format = '%(asctime)s :: %(levelname)s :: %(message)s'
formatter = logging.Formatter(log_format)
file_handler = RotatingFileHandler(logfile, 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def parse_commit_message(message, issue_reg):
    """Parse the commit message

    :returns: The redmine issue ID
              or None if there is no Issue reference
    """
    m = issue_reg.findall(message)
    if not m:
        return None
    # Only match the first mentionned bug
    return m[0][1]


class GerritHook(object):
    """Base for gerrit hooks"""

    def __init__(self, cli_options=None, conf_file=None):
        self.command_line_options = cli_options or DEFAULT_CLI_OPTIONS
        self.conf_file = conf_file
        self.config = yaml.load(conf_file)
        self.redmine_client = RedmineUtils(self.config['redmine_url'],
                                           key=self.config['redmine_key'])
        bottom_url = "/_r/gitweb?p=%(project)s;a=commit;h=%(commit)s"
        self.gitweb_url = urllib_parse.urljoin(self.config['gitweb_url'],
                                               bottom_url)

    def get_parser(self):
        parser = argparse.ArgumentParser()
        for arg in self.command_line_options:
            parser.add_argument('--%s' % arg)
        return parser

    def get_trimmed_commit(self, commit):
        # We remove the fourth first lines of the commit message
        # tree, parent, author, committer and we just keep
        # the real user message
        commit_msg = subprocess.check_output(['git', 'cat-file',
                                              '-p', commit])
        return "\n".join(commit_msg.splitlines()[4:])

    def get_issue(self, commit, regexp):
        # GIT_SSH env var is setup by Gerrit when calling the hook
        commit_msg = subprocess.check_output(['git', 'cat-file',
                                              '-p', commit])
        return parse_commit_message(commit_msg, regexp)

    def main(self, args):
        error_code = 0
        commit_msg = self.get_trimmed_commit(args.commit)
        # Build message for the issue
        gitweb = self.gitweb_url % {'project': args.project + '.git',
                                    'commit': args.commit}
        message = self.msg % {'branch': args.branch,
                              'url': args.change_url,
                              'submitter': getattr(args, 'submitter', ''),
                              'commit': commit_msg,
                              'gitweb': gitweb}
        closing_issue = self.get_issue(args.commit, CLOSING_ISSUE)
        related_issue = self.get_issue(args.commit, RELATED_ISSUE)
        if closing_issue:
            if not self.redmine_client.set_issue_status(closing_issue,
                                                        self.status_closing,
                                                        message=message):
                msg = "Could not close issue #%s" % closing_issue
                logger.error(msg)
                error_code = 1
        if related_issue and related_issue != closing_issue:
            if not self.redmine_client.set_issue_status(related_issue,
                                                        self.status_related,
                                                        message=message):
                msg = "Could not update issue #%s" % closing_issue
                logger.error(msg)
                error_code = 1
        if not related_issue and not closing_issue:
            logger.debug("No issue mentioned, nothing to do.")
        return error_code
