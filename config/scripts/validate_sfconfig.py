#!/usr/bin/python

from sys import argv
import yaml

try:
    d = yaml.load(open(argv[1]))
except:
    print "usage: %s sfconfig.yaml" % argv[0]
    raise

# Adds default values and validation here

# Remove admin_name config option (2.0.1 -> 2.0.2)
if "admin_name" in d["authentication"]:
    if d["authentication"]["admin_name"] != "admin":
        print "Change admin name to 'admin'"
        exit(1)
    del d["authentication"]["admin_name"]

# Remove public_ip setting of nodepool (2.0.1 -> 2.0.2)
if 'public_ip' in d['nodepool']:
    del d['nodepool']['public_ip']

# Use disabled key instead (2.0.1 -> 2.0.2)
if 'swift_logsexport_activated' in d['logs']:
    del d['logs']['swift_logsexport_activated']

# Change nodepool setting structure (2.0.1 -> 2.0.2)
nodepool = d['nodepool']
if not 'providers' in nodepool:
    mapping = {'nodepool_os_username': 'username',
               'nodepool_os_password': 'password',
               'nodepool_os_project_id': 'project-id',
               'nodepool_os_auth_url': 'auth-url',
               'nodepool_os_pool': 'pool',
               'nodepool_os_pool_max_amount': 'max-servers',
               'nodepool_provider_rate': 'rate'}
    nodepool['providers'] = []
    provider = {'name': 'default'}
    for k, v in mapping.items():
        provider[v] = nodepool[k]
        del nodepool[k]
    nodepool['providers'].append(provider)

yaml.dump(d, open(argv[1], "w"), default_flow_style=False)
exit(0)
