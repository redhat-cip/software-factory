from os import environ

ADMIN_USER = 'fabien.boucher'
ADMIN_PASSWD = 'userpass'
ADMIN_EMAIL = 'fabien.boucher@enovance.com'
ADMIN_PRIV_KEY_PATH = '%s/build/data/gerrit_admin_rsa' % environ['SF_ROOT']

GERRIT_HOST = '%s-gerrit:29418' % environ['SF_PREFIX']
GERRIT_SERVER = 'http://%s-gerrit/r/' % environ['SF_PREFIX']
REDMINE_SERVER = 'http://%s-redmine' % environ['SF_PREFIX']
