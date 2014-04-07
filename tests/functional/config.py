from os import environ

ADMIN_USER = 'fabien.boucher'
ADMIN_PASSWD = 'userpass'
ADMIN_EMAIL = 'fabien.boucher@enovance.com'
ADMIN_PRIV_KEY_PATH = '%s/build/data/gerrit_admin_rsa' % environ['SF_ROOT']

GERRIT_HOST = 'tests-gerrit:29418'
