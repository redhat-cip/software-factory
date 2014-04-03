# Server Specific Configurations
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
        'host': 'ldap://sf-ldap',
        'dn': 'cn=%(username)s,ou=Users,dc=enovance,dc=com'
    }
}

gerrit = {
    'host': 'sf-gerrit',
    'admin': 'fabien.boucher',
    'admin_email': 'fabien.boucher@enovance.com',
    'ssh_port': 29418,
    'http_password': 'userpass',
    'sshkey_priv_path': '/srv/SoftwareFactory/build/data/gerrit_admin_rsa'
}

redmine = {
    'host': 'sf-redmine',
    'api_key': '7f094d4e3e327bbd3f67279c95c193825e48f59e'
}
# Custom Configurations must be in Python dictionary format::
#
# foo = {'bar':'baz'}
#
# All configurations are accessible at::
# pecan.conf
