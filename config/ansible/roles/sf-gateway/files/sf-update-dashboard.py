#!/bin/env python
# Convert dash files to json representation for custom dashboard

import ConfigParser
import argparse
import json
import os
import requests
import urllib
import sys


def usage(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="/root/config/dashboards")
    p.add_argument("--output", default="/var/www/dashboards_data")
    p.add_argument("--check", default=False, action='store_true')
    p.add_argument("--managesf-url")
    return p.parse_args(argv)


def load_dashboard(path, title=None, extra_foreach=None):
    # Load dash file
    dash = ConfigParser.SafeConfigParser()
    dash.readfp(open(path))
    data = {
        'title': dash.get('dashboard', 'title') if title is None else title,
        'description': dash.get('dashboard', 'description'),
        'tables': []
    }
    foreach = dash.get('dashboard', 'foreach')
    if extra_foreach:
        foreach = "%s %s" % (foreach, extra_foreach)
    sections = []
    for section in dash.sections():
        if section.startswith('section "'):
            sections.append((section[9:-1], dash.get(section, 'query')))

    # Generate gerrit dashboard url
    qs = []
    if foreach:
        qs.append(('foreach', foreach))
    qs.append(('title', data['title']))
    for section in sections:
        qs.append(section)
    data['gerrit_url'] = '/r/#/dashboard/?%s' % urllib.urlencode(qs)

    # Generate gerrit changes query
    gerrit_query = []
    for table, query in sections:
        data['tables'].append(table)
        if foreach:
            query = "%s %s" % (query, foreach)
        gerrit_query.append(urllib.quote_plus(query))

    data['gerrit_query'] = '/r/changes/?q=%s&O=81' % "&q=".join(gerrit_query)
    return data


def main(argv=sys.argv[1:]):
    args = usage(argv)
    # Generate data for each dash file
    dashboards = {}
    for dashboard in filter(lambda x: x.endswith(".dash"),
                            os.listdir(args.input)):
        dashboard_file = "%s/%s" % (args.input, dashboard)
        try:
            data = load_dashboard(dashboard_file)
        except Exception, e:
            print("[E] Couldn't load %s: %s" % (dashboard_file, e))
            if args.check:
                exit(1)
            continue
        dashboards[dashboard.replace('.dash', '')] = data

    if args.check:
        return

    if args.managesf_url:
        for name, project in requests.get("%s/resources" % args.managesf_url) \
                .json().get('resources', {}).get('projects', {}).items():
            if not project.get('review-dashboard'):
                continue
            dashboard_file = "%s/%s.dash" % (
                args.input, project.get('review-dashboard'))
            if not os.path.isfile(dashboard_file):
                print("[E] Couldn't find dashboard named %s" %
                      project.get('review-dashboard'))
                continue
            foreach = "(%s)" % (" OR ".join(map(lambda x: 'project:%s' % x,
                                project.get('source-repositories'))))
            try:
                data = load_dashboard(dashboard_file,
                                      title="%s's dashboard" % name,
                                      extra_foreach=foreach)
            except Exception, e:
                print("[E] Couldn't load dashboard: %s" % e)
                continue
            dashboards['project_%s' % name] = data

    dashboards_list = []
    for name, data in sorted(list(dashboards.items())):
        dashboards_list.append({
            'name': name,
            'title': data['title'],
            'description': data['description']
        })

    with open("%s/data.json" % args.output, "wb") as of:
        of.write(json.dumps(dashboards_list))

    for name, data in dashboards.items():
        with open("%s/data_%s.json" % (args.output, name), "wb") as of:
            of.write(json.dumps(data))
if __name__ == "__main__":
    main()
