#!/usr/bin/python

import yaml
import uuid
import subprocess

# from:
# http://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data # flake8: noqa
def should_use_block(value):
    for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False


def my_represent_scalar(self, tag, value, style=None):
    if style is None:
        if should_use_block(value):
            style = '|'
        else:
            style = self.default_style

    node = yaml.representer.ScalarNode(tag, value, style=style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    return node

yaml.representer.BaseRepresenter.represent_scalar = my_represent_scalar
# end from
# from: http://pyyaml.org/ticket/64
class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
# end from


creds = yaml.load(open("/etc/software-factory/sfcreds.yaml").read())

sqls = []
fqdn = yaml.load(open("/etc/software-factory/sfconfig.yaml").read())['fqdn']

for user in ('redmine', 'gerrit', 'nodepool', 'etherpad', 'lodgeit', 'graphite', 'grafana', 'cauth', 'managesf'):
    key = "creds_%s_sql_pwd" % user
    pwd = str(uuid.uuid4())

    # Allow connection from remote services
    if user == 'redmine':
        sqls.append("SET PASSWORD FOR '%s'@'redmine.%s' = PASSWORD('%s');" % (
            user, fqdn, pwd
        ))
    elif user == 'gerrit':
        sqls.append("SET PASSWORD FOR '%s'@'gerrit.%s' = PASSWORD('%s');" % (
            user, fqdn, pwd
        ))
    elif user == 'nodepool':
        sqls.append("SET PASSWORD FOR '%s'@'nodepool.%s' = PASSWORD('%s');" % (
            user, fqdn, pwd
        ))
    elif user == 'grafana':
        sqls.append("SET PASSWORD FOR '%s'@'statsd.%s' = PASSWORD('%s');" % (
            user, fqdn, pwd
        ))

    # Always allow connection from managesf for all-in-one compatibility
    sqls.append("SET PASSWORD FOR '%s'@'managesf.%s' = PASSWORD('%s');" % (
        user, fqdn, pwd
    ))
    creds[key] = pwd

open("/etc/software-factory/sfcreds.yaml", "w").write(yaml.dump(creds, default_flow_style=False, Dumper=MyDumper))
ret = subprocess.Popen(["mysql", "-e",  " ".join(sqls)]).wait()
if ret:
    print "Error: Couldn't update database passwords... (rc: %d)" % ret
exit(subprocess.Popen(["sfconfig.sh"]).wait())
