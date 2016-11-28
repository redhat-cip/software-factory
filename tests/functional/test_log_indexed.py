#!/bin/env python
#
# Copyright (2016) Red Hat
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

import shlex
import config
import random
import string
import json
import datetime
import time

from utils import Base, skipIfServiceMissing
from utils import set_private_key
from utils import GerritGitUtils
from subprocess import Popen, PIPE


class TestLogExportedInElasticSearch(Base):
    """ Functional tests to verify job logs are exported in ElasticSearch
    """
    def setUp(self):
        super(TestLogExportedInElasticSearch, self).setUp()
        self.un = config.ADMIN_USER
        self.priv_key_path = set_private_key(config.USERS[self.un]["privkey"])
        self.gitu_admin = GerritGitUtils(self.un,
                                         self.priv_key_path,
                                         config.USERS[self.un]['email'])

    def run_ssh_cmd(self, sshkey_priv_path, user, host, subcmd):
        host = '%s@%s' % (user, host)
        sshcmd = ['ssh', '-o', 'LogLevel=ERROR',
                  '-o', 'StrictHostKeyChecking=no',
                  '-o', 'UserKnownHostsFile=/dev/null', '-i',
                  sshkey_priv_path, host]
        cmd = sshcmd + subcmd

        p = Popen(cmd, stdout=PIPE)
        return p.communicate(), p.returncode

    def push_request_script(self, index, newhash):
        newhash = newhash.rstrip()
        content = """
curl -s -XPOST 'http://elasticsearch.%s:9200/%s/_search?pretty&size=1' -d '{
      "query": {
          "bool": {
              "must": [
                  { "match": { "build_name": "config-update" } },
                  { "match": { "build_newrev": "%s" } }
              ]
          }
      }
}'
"""
        with open('/tmp/test_request.sh', 'w') as fd:
            fd.write(content % (config.GATEWAY_HOST, index, newhash))
        cmd = ['scp', '/tmp/test_request.sh',
               'root@%s:/tmp/test_request.sh' % config.GATEWAY_HOST]
        p = Popen(cmd, stdout=PIPE)
        return p.communicate(), p.returncode

    def find_index(self):
        subcmd = "curl -s -XGET http://elasticsearch.%s:9200/_cat/indices" % (
            config.GATEWAY_HOST)
        subcmd = shlex.split(subcmd)
        # A logstash index is created by day
        today_str = datetime.datetime.utcnow().strftime('%Y.%m.%d')
        # Here we fetch the index name, but also we wait for
        # it to appears in ElasticSearch for 5 mins
        index = []
        for retry in xrange(300):
            try:
                out = self.run_ssh_cmd(config.SERVICE_PRIV_KEY_PATH, 'root',
                                       config.GATEWAY_HOST, subcmd)
                outlines = out[0][0].split('\n')
                outlines.pop()
                index = [o for o in outlines if
                         o.split()[2].startswith('logstash-%s' % today_str)]
                if len(index):
                    break
            except:
                time.sleep(1)
        self.assertEqual(
            len(index),
            1,
            "No logstash index has been found for today logstash-%s (%s)" % (
                today_str, str(index)))
        index = index[0].split()[2]
        return index

    def verify_logs_exported(self):
        subcmd = "bash /tmp/test_request.sh"
        subcmd = shlex.split(subcmd)
        for retry in xrange(300):
            out = self.run_ssh_cmd(config.SERVICE_PRIV_KEY_PATH, 'root',
                                   config.GATEWAY_HOST, subcmd)
            ret = json.loads(out[0][0])
            if len(ret['hits']['hits']) >= 1:
                break
            elif len(ret['hits']['hits']) == 0:
                time.sleep(1)
        self.assertEqual(len(ret['hits']['hits']),
                         1,
                         "Fail to find our log in ElasticSeach")
        return ret['hits']['hits'][0]

    def direct_push_in_config_repo(self, url, pname='config'):
        rand_str = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(5))
        clone = self.gitu_admin.clone(url, pname)
        with open('%s/test_%s' % (clone, rand_str), 'w') as fd:
            fd.write('test')
        self.gitu_admin.add_commit_in_branch(
            clone, 'master', ['test_%s' % rand_str])
        head = file('%s/.git/refs/heads/master' % clone).read()
        self.gitu_admin.direct_push_branch(clone, 'master')
        return head

    @skipIfServiceMissing('elasticsearch')
    def test_log_indexation(self):
        """ Test job log are exported in Elasticsearch
        """
        head = self.direct_push_in_config_repo(
            'ssh://admin@%s:29418/config' % (
                config.GATEWAY_HOST))
        index = self.find_index()
        self.push_request_script(index, head)
        log = self.verify_logs_exported()
        self.assertEqual(log['_source']["build_name"], "config-update")
