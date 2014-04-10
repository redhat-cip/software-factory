from os import environ

ADMIN_USER = 'user1'
ADMIN_PASSWD = 'userpass'
ADMIN_EMAIL = 'user1@example.com'
ADMIN_PRIV_KEY_PATH = '%s/build/data/gerrit_admin_rsa' % environ['SF_ROOT']

GERRIT_HOST = '%s-gerrit:29418' % environ['SF_PREFIX']
GERRIT_SERVER = 'http://%s-gerrit/r/' % environ['SF_PREFIX']
REDMINE_SERVER = 'http://%s-redmine' % environ['SF_PREFIX']
MANAGESF_HOST = '%s-managesf' % environ['SF_PREFIX']
