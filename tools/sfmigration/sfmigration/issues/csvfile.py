#!/usr/bin/python
#
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

import csv

from sfmigration.common import base
from sfmigration.common import utils


logger = utils.logger


REDMINE_ISSUE_FIELDS = [
    'source_id',
    'subject',
    'description',
    'tracker_id',
    'tracker_name',
    'status_id',
    'status_name',
    'priority_id',
    'priority_name',
    'done_ratio',
    'story_points',
    'fixed_version_id',
    'version_name',
    'assigned_to_id',
    'assigned_to_login',
]


class CSVImporter(base.BaseIssueImporter):

    def __init__(self, csv_file, fieldnames=None, fieldnames_mapping={}):
        with open(csv_file, 'rb') as c:
            sniffer = csv.Sniffer()
            self.skip_header_line = sniffer.has_header(c.read(1024))
            if not self.skip_header_line and not fieldnames:
                raise ValueError('The CSV document has no field names'
                                 ' and cannot be parsed')
            c.seek(0)
            self.dialect = sniffer.sniff(c.read(4096))
        self.csv_file = csv_file
        self.mapping = fieldnames_mapping or {}
        if fieldnames:
            self.fieldnames = fieldnames
            # since fieldnames are provided, assume there are no header lines
            self.skip_header_line = False
        else:
            with open(csv_file, 'rb') as c:
                csv_dict = csv.DictReader(c,
                                          dialect=self.dialect)
                # read the first object to initialize the fieldnames property
                csv_dict.next()
                self.fieldnames = csv_dict.fieldnames

    def fetch_issues(self):
        with open(self.csv_file) as c:
            issue_dict = csv.DictReader(c,
                                        fieldnames=self.fieldnames,
                                        dialect=self.dialect)
            first_line = True
            for issue in issue_dict:
                if self.skip_header_line and first_line:
                    first_line = False
                    continue
                # dummy initial values to be safe
                issue_data = {'source_id': 0,
                              'priority_id': 1}
                for field in REDMINE_ISSUE_FIELDS:
                    if self.mapping.get(field, field) in self.fieldnames:
                        issue_data[field] = issue[self.mapping.get(field,
                                                                   field)]
                yield issue_data

    def fetch_versions(self):
        # We fetch the milestones from the issues csv. This is a best guess.
        versions = {}
        with open(self.csv_file) as c:
            issue_dict = csv.DictReader(c,
                                        fieldnames=self.fieldnames,
                                        dialect=self.dialect)
            first_line = True
            for issue in issue_dict:
                if self.skip_header_line and first_line:
                    first_line = False
                    continue
                version_name = issue.get(self.mapping.get('version_name',
                                                          'version_name'),
                                         None)
                version_id = issue.get(self.mapping.get('fixed_version_id',
                                                        'fixed_version_id'),
                                       None)
                versions[version_name] = version_id
        for name, id in versions.items():
            if name:
                version_data = {'source_id': id}
                version_data['name'] = name
                # default status
                version_data['status'] = 'open'
                yield version_data
