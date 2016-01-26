#!/usr/bin/python

from sys import argv
import yaml

try:
    d = yaml.load(open(argv[1]))
except:
    print "usage: %s sfconfig.yaml" % argv[0]
    raise


# Migration from 2.0.0 to >2.0.0 configuration format
def migrate_2_0_0():
    sfconfig = yaml.load(open('config/defaults/sfconfig.yaml'))

    def update(dst, keys):
        for k in keys:
            dst[k] = d[k]

    sfconfig['fqdn'] = d['domain']

    # network
    update(sfconfig['network'], ('enforce_ssl', 'smtp_relay',
                                 'ntp_main_server'))
    sfconfig['network']['admin_mail_forward'] = d['admin_mail']

    # authentication
    update(sfconfig['authentication'], ('admin_name', 'admin_password',
                                        'sso_cookie_timeout',
                                        'authenticated_only'))
    update(sfconfig['authentication']['ldap'], (
        'ldap_url', 'ldap_account_base', 'ldap_account_username_attribute',
        'ldap_account_mail_attribute', 'ldap_account_surname_attribute'))

    update(sfconfig['authentication']['github'],
           ('github_app_id', 'github_app_secret',
            'github_allowed_organizations'))

    # misc
    update(sfconfig['theme'], ('loginpage_custom_footer', 'topmenu_logo_style',
                               'topmenu_logo_data', 'favicon_data',
                               'topmenu_hide_redmine'))
    update(sfconfig['backup'], ('os_auth_url', 'os_tenant_name', 'os_username',
                                'os_password', 'swift_backup_container',
                                'swift_backup_max_retention_secs'))
    update(sfconfig['nodepool'], (
        'nodepool_os_username', 'nodepool_os_password',
        'nodepool_os_project_id', 'nodepool_os_auth_url', 'nodepool_os_pool',
        'nodepool_os_pool_max_amount', 'public_ip', 'nodepool_provider_rate'))

    update(sfconfig['logs'], (
        'swift_logsexport_activated', 'swift_logsexport_container',
        'swift_logsexport_logserver_prefix', 'swift_logsexport_authurl',
        'swift_logsexport_x_storage_url', 'swift_logsexport_username',
        'swift_logsexport_password', 'swift_logsexport_tenantname',
        'swift_logsexport_authversion', 'swift_logsexport_x_tempurl_key',
        'swift_logsexport_send_tempurl_key'))

    return sfconfig

if "domain" in d:
    d = migrate_2_0_0()

# Remove admin_name config option (2.0.1 -> 2.0.2)
if "admin_name" in d["authentication"]:
    if d["authentication"]["admin_name"] != "admin":
        print "Please change admin name to 'admin' first (re-run sfconfig.sh)"
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
if 'providers' not in nodepool:
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

# Adds ldap disabled settings
ldap = d['authentication']['ldap']
if "disabled" not in ldap:
    if ldap['ldap_url'] not in ('', 'ldap://sftests.com'):
        ldap['disabled'] = False
    else:
        ldap['disabled'] = True

github = d['authentication']['github']
if "disabled" not in github:
    if github['github_app_id']:
        github['disabled'] = True
    else:
        github['disabled'] = False

if not d['authentication'].get('launchpad'):
    d['authentication']['launchpad'] = {'disabled': False}

# Make sure backup has os_auth_version (2.0.4 -> 2.1.0)
if "os_auth_version" not in d["backup"]:
    d["backup"]["os_auth_version"] = 1

yaml.dump(d, open(argv[1], "w"), default_flow_style=False)
exit(0)
