#!/usr/bin/env python
# Copyright 2013 OpenStack Foundation
# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

import urllib2
import json
import argparse
import os
import time


if not os.path.isfile("/etc/zuul/zuul.conf"):
    print "This script needs to be run from zuul node"
    exit(1)

# Read zuul_url from zuul.conf
zuul_url = filter(lambda x: x.startswith("zuul_url="),
                  open("/etc/zuul/zuul.conf").readlines())[0].split('=')[1]
# Remove /p
zuul_status = "%s/status.json" % ('/'.join(zuul_url.split('/')[:-1]))
dump_file = "/var/lib/zuul/zuul-queues-dump.sh"


def dump(args):
    data = urllib2.urlopen(args.url).read()
    data = json.loads(data)

    if os.path.isfile(args.dump_file):
        os.rename(args.dump_file, "%s.orig" % args.dump_file)

    of = open(args.dump_file, "w")
    of.write("#/bin/sh\nset -ex\n")
    for pipeline in data['pipelines']:
        for queue in pipeline['change_queues']:
            for head in queue['heads']:
                for change in head:
                    if not change['live'] or ',' not in change['id']:
                        continue
                    cid, cps = change['id'].split(',')
                    cmd = (
                        "zuul enqueue --trigger gerrit --pipeline %s "
                        "--project %s --change %s,%s" % (
                            pipeline['name'],
                            change['project'],
                            cid, cps)
                    )
                    if ";" in cmd or "|" in cmd:
                        raise RuntimeError("Forbidden char in [%s]" % cmd)
                    print cmd
                    of.write("%s\n" % cmd)
    of.write("curl %s 2>&1 | grep 'zuul_version' > /dev/null\n" % args.url)
    of.write("echo SUCCESS: zuul queues restored\n")
    of.close()
    os.chmod(args.dump_file, 0755)


def load(args):
    if not os.path.isfile(args.dump_file):
        print "%s: no such file, please dump first" % args.dump_file
    if os.stat(args.dump_file).st_mtime + 172800 < time.time():
        if not args.force:
            raise RuntimeError("%s is too old, use --force to use it" %
                               args.dump_file)
    os.system(dump_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action="store_const", const=True)
    parser.add_argument('--url', default=zuul_status)
    parser.add_argument('--dump_file', default=dump_file)
    parser.add_argument('action', choices=("dump", "load"))
    args = parser.parse_args()
    if args.action == "dump":
        dump(args)
    else:
        load(args)
