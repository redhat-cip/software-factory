#!/usr/bin/python

import ConfigParser
from github import Github, GithubException
import os.path
from redmine import Redmine
import string
import sys


def get_config_value(section, option):
    cp = ConfigParser.ConfigParser()
    cp.read('config.ini')
    try:
        return cp.get(section, option)
    except:
        return None


def main():
    #check config file is present or not
    if not os.path.isfile('config.ini'):
        print "ERROR :: config file is missing"
        sys.exit(1)

    #read the config file and populate the data
    github = {'git_username': '', 'git_password': '', 'repos': ''}
    for key in github.iterkeys():
        github[key] = get_config_value('GITHUB', key)

    redmine = {'rm_username': '', 'rm_password': '', 'id': '',
               'apikey': '', 'url': '', 'name': ''}
    for key in redmine.iterkeys():
        redmine[key] = get_config_value('REDMINE', key)

    #if url edswith backslash, remove it before use.
    if redmine['url'].endswith('/'):
        redmine['url'] = redmine['url'][:-1]

    if github['git_username'] is not None and\
       github['git_password'] is not None:
        g = Github(github['git_username'], github['git_password'])
    else:
        g = Github()

    if redmine['apikey'] is not None or redmine['apikey'] != '':
        r = Redmine(redmine['url'], key = redmine['apikey'])
    else:
        r = Redmine(redmine['url'], username = redmine['rm_username'],
                    password = redmine['rm_password'])

    #if project id not given, find
    if redmine['id'] is None:
        projects = r.project.all()
        for p in projects:
            if p.name == redmine['name']:
                redmine['id'] = p.id
    if redmine['id'] is None:
        print "ERROR : given project name is not found"
        sys.exit(1)
    if redmine['name'] is None:
        redmine['name'] = r.project.get(redmine['id'])

    issue_count = 0
    for repo in string.split(github['repos']):
        try:
            rep = g.get_repo(repo)
            issues = rep.get_issues(state = 'all')
            for i in issues:
                subject = i.title
                description = i.body
                if i.state == 'closed':
                    status_id = 5
                else:
                    status_id = 1
                try:
                    r.issue.create(project_id = redmine['id'],
                                   subject = subject,
                                   tracker_id = 1,
                                   status_id = status_id,
                                   priority_id = 4,
                                   description = description)
                except Exception:
                    continue
                issue_count = issue_count + 1
        except GithubException as ge:
            print "ERROR : not able to get issue for %s" % repo
            print "ERROR Message :\n", ge

    print '\n{0} issues are created in project {1}'.format(issue_count,
                                                           redmine['name'])

if __name__ == '__main__':
    main()
