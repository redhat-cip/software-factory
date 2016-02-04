#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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

import os
import sys
import time
import requests


round_delay = 20


def log(msg):
    sys.stdout.write("%s\n" % str(msg))
    sys.stdout.flush()


def look_for_my_change(gate, cid):
    for queue in gate['change_queues']:
        if queue['heads']:
            for head in queue['heads']:
                for change in head:
                    if change['id'].split(',')[0] == cid:
                        log("Found change in shared queue: " +
                            "%s" % queue['name'])
                        return change


def check_jobs_status(my_change):
    status = {}
    for job in my_change['jobs']:
        if job['name'] == myname:
            continue
        status[job['name']] = None
        if job['end_time']:
            log("Job: %s terminated with status: %s" % (
                job['name'], job['result']))
        else:
            log("Job: %s still running" % job['name'])
            status[job['name']] = 2
            continue
        if job['result'] == 'SUCCESS':
            status[job['name']] = 0
        else:
            status[job['name']] = 1
    return status


def fetch_get_pipeline_status(host):
    log("Fetching Zuul status")
    r = requests.get("%s/status.json" % host).json()
    return [pipeline for pipeline in r['pipelines'] if
            pipeline['name'] == 'gate'][0]


def check_non_voting(status, my_change):
    for k, v in status.items():
        if v == 1:
            job = [j for j in my_change['jobs'] if j['name'] == k][0]
            if job['voting']:
                log("Job: %s is voting !" % k)
                return False
    return True


if __name__ == "__main__":
    host = os.environ['ZUUL_URL'].rstrip('/p')
    myname = os.environ['JOB_NAME']
    change = os.environ['ZUUL_CHANGE']
    while True:
        log("")
        gate = fetch_get_pipeline_status(host)
        my_change = look_for_my_change(gate, change)
        if not my_change:
            log("Error. Change does not exists !")
            sys.exit(1)
        if my_change['item_ahead'] is None:
            log("Found current jobs running along with me")
            status = check_jobs_status(my_change)
            if len([v for v in status.values() if v == 0]) == \
               len(my_change['jobs']) - 1:
                log("All jobs succeed for this change")
                break
            elif len([v for v in status.values() if v == 2]):
                log("At least one job is in progress. Waiting ...")
                time.sleep(round_delay)
                continue
            else:
                if check_non_voting(status, my_change):
                    log("All jobs in failure are non voting")
                    break
                else:
                    log("Jobs finished but at least one voting job failed")
                    sys.exit(1)
        else:
            log("Change is not ahead of the shared queue. waiting ...")
            time.sleep(round_delay)
