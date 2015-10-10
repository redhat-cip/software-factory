#!/usr/bin/python

from sys import argv
from yaml import load, dump

try:
    oldconfig = load(open(argv[1]))
    sfconfig = load(open(argv[2]))
except:
    print "usage: %s config_path new_template" % (argv[0])
    raise


def update(d, keys):
    for k in keys:
        d[k] = oldconfig[k]

sfconfig['fqdn'] = oldconfig['domain']

# network
update(sfconfig['network'], ('enforce_ssl', 'smtp_relay', 'ntp_main_server'))
sfconfig['network']['admin_mail_forward'] = oldconfig['admin_mail']

# authentication
update(sfconfig['authentication'], ('admin_name', 'admin_password',
                                    'sso_cookie_timeout',
                                    'authenticated_only'))
update(sfconfig['authentication']['ldap'], (
    'ldap_url', 'ldap_account_base', 'ldap_account_username_attribute',
    'ldap_account_mail_attribute', 'ldap_account_surname_attribute'))

update(sfconfig['authentication']['github'],
       ('github_app_id', 'github_app_secret', 'github_allowed_organizations'))

# misc
update(sfconfig['theme'], ('loginpage_custom_footer', 'topmenu_logo_style',
                           'topmenu_logo_data', 'favicon_data',
                           'topmenu_hide_redmine'))
update(sfconfig['backup'], ('os_auth_url', 'os_tenant_name', 'os_username',
                            'os_password', 'swift_backup_container',
                            'swift_backup_max_retention_secs'))
update(sfconfig['nodepool'], (
    'nodepool_os_username', 'nodepool_os_password', 'nodepool_os_project_id',
    'nodepool_os_auth_url', 'nodepool_os_pool', 'nodepool_os_pool_max_amount',
    'public_ip', 'nodepool_provider_rate'))

update(sfconfig['logs'], (
    'swift_logsexport_activated', 'swift_logsexport_container',
    'swift_logsexport_logserver_prefix', 'swift_logsexport_authurl',
    'swift_logsexport_x_storage_url', 'swift_logsexport_username',
    'swift_logsexport_password', 'swift_logsexport_tenantname',
    'swift_logsexport_authversion'))

dump(sfconfig, open(argv[1], 'w'), default_flow_style=False)
