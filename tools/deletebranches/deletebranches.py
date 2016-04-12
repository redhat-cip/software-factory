#!/usr/bin/env python
import argparse
import json
import requests
import sys


def status(ok, last=False):
    if ok:
        sys.stdout.write('+')
    else:
        sys.stdout.write('-')
    if last:
        print ""


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Delete branches')
    parser.add_argument('-u', '--user', type=str, required=True,
                        help='Gerrit username')
    parser.add_argument('-p', '--password', type=str, required=True,
                        help='Gerrit HTTP password')
    parser.add_argument('-o', '--org', type=str, required=True,
                        help='Github organization name')
    parser.add_argument('-t', '--token', type=str, required=True,
                        help='Github token')
    parser.add_argument('-b', '--branch', type=str, required=True,
                        help='Branch to delete')
    parser.add_argument('-d', '--default-branch', type=str, required=False,
                        help='New default branch')
    parser.add_argument('-f', '--filter', type=str, required=True,
                        help='Projectname filter, for example "-distgit"')
    parser.add_argument('--host', type=str, required=True,
                        help='Gerrit host, for example sftests.com')
    parser.add_argument('-n', '--no-op', action='store_true', required=False,
                        help='Do not delete repos, only print actions')
    args = parser.parse_args(argv)

    if args.branch == "master" and not args.default_branch:
        raise parser.error(
            "Need a new default branch if master will be deleted")

    url = "http://%s:%s@%s/api/a/projects/" % (
        args.user, args.password, args.host)
    resp = requests.get(url)
    projects = json.loads(resp.content[4:])

    for project_name in projects.keys():
        if project_name.endswith(args.filter):
            if not args.no_op:
                print "Deleting branch %s on project %s: " % (
                    args.branch, project_name),

                if args.default_branch:
                    headers = {'Authorization': 'token %s' % args.token,
                               'Content-Type': 'application/json'}
                    data = json.dumps(
                        {"ref": "refs/heads/%s" % args.default_branch})
                    gerrit_url = "http://%s:%s@%s/api/a/projects/%s/HEAD" % (
                        args.user, args.password, args.host, project_name)
                    resp = requests.put(gerrit_url, headers=headers, data=data)
                    status(resp.ok)

                    data = json.dumps(
                        {"name": "%s" % project_name,
                         "default_branch": "%s" % args.default_branch})
                    github_url = "https://api.github.com/repos/%s/%s" % (
                        args.org, project_name)
                    resp = requests.patch(
                        github_url, headers=headers, data=data)
                    status(resp.ok)

                headers = {'Authorization': 'token %s' % args.token}
                gerrit_url = \
                    "http://%s:%s@%s/api/a/projects/%s/branches/%s" % (
                        args.user, args.password,
                        args.host, project_name, args.branch)
                resp = requests.delete(gerrit_url, headers=headers)
                status(resp.ok)

                github_url = \
                    "https://api.github.com/repos/%s/%s/git/refs/heads/%s" % (
                        args.org, project_name, args.branch)
                resp = requests.delete(github_url, headers=headers)
                status(resp.ok, True)
            else:
                print "Would delete branch %s on project %s" % (
                    args.branch, project_name)


if __name__ == '__main__':
    main()
