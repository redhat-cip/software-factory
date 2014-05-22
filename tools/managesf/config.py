#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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
# Server Specific Configurations
import os

server = {
    'port': '9090',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'managesf.controllers.root.RootController',
    'modules': ['managesf'],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/managesf/templates',
    'debug': True,
}

logging = {
    'loggers': {
        'root': {'level': 'INFO', 'handlers': ['console']},
        'managesf': {'level': 'DEBUG', 'handlers': ['console']},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        }
    }
}

# Authorization configurations
auth = {
    'type': 'ldap',
    'ldap': {
        'host': 'ldap://ldap.%s' % (os.environ['SF_SUFFIX']),
        'dn': 'cn=%(username)s,ou=Users,dc=example,dc=com'
    }
}

gerrit = {
    'host': 'gerrit.%s' % (os.environ['SF_SUFFIX']),
    'admin': 'user1',
    'admin_email': 'user1@example.com',
    'ssh_port': 29418,
    'http_password': 'userpass',
    'sshkey_priv_path': '%s/build/data/gerrit_admin_rsa' %
    (os.environ['SF_ROOT'])
}

redmine = {
    'host': 'redmine.%s' % (os.environ['SF_SUFFIX']),
    'api_key': '7f094d4e3e327bbd3f67279c95c193825e48f59e'
}
# Custom Configurations must be in Python dictionary format::
#
# foo = {'bar':'baz'}
#
# All configurations are accessible at::
# pecan.conf
