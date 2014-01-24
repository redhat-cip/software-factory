#scp -r puppet $1:.
#ssh $1 "cd puppet ; FACTER_REDMINE_DATABASE_ADAPTER=mysql FACTER_REDMINE_DATABASE_NAME=redmine FACTER_REDMINE_DATABASE_HOST=localhost FACTER_REDMINE_DATABASE_USERNAME=root FACTER_REDMINE_DATABASE_PASSWORD=root puppet apply --modulepath modules/ redmine_node.pp"

cd puppet
# Where repo are store in the FS
export FACTER_REPO_BASE_PATH="git"

# Gerrit WEB UI address
export FACTER_WEBURL="http://198.154.188.164:9999"
# Can be use to set GIT read access from a mirror
export FACTER_GITURL="git://mirror.monrepo.local"
# Can be use to set HTTP read access from a mirror
export FACTER_HTTPURL="http://mirror.monrepo.local"
# Bug tracker URL
export FACTER_REPORTBUGURL="http://redmine.monrepo.local"

export FACTER_SSHD_LISTEN_ADDRESS="*:29418"
export FACTER_HTTP_LISTEN_ADDRESS="http://*:9999"

export FACTER_EMAIL_PRIVATE_KEY="test@local"

export FACTER_MYSQL_ADDRESS="127.0.0.1"
export FACTER_GERRIT_MYSQL_DB="reviewdb"
export FACTER_GERRIT_MYSQL_USERNAME="gerrit2"
export FACTER_MYSQL_POST="3306"
export FACTER_GERRIT_MYSQL_SECRET="secret"

export FACTER_LDAP_ADDRESS="ldap://127.0.0.1"
export FACTER_LDAP_USERNAME="uid=fbo,ou=people,dc=novalocal"
export FACTER_LDAP_PASSWORD="wxcvbn_fbo"
export FACTER_LDAP_ACCOUNT_BASE="ou=people,dc=novalocal"
export FACTER_LDAP_ACCOUNT_PATTERN='(&(objectClass=posixAccount)(uid=${username}))'
export FACTER_LDAP_ACCOUNT_EMAIL_ADDRESS='mail'
export FACTER_HTTP_BASIC_AUTH='true'

#export FACTER_LDAP_GROUP_BASE="ou=groups,dc=novalocal"
#export FACTER_LDAP_GROUP_PATTERN='(&(objectClass=posixGroup)(cn=${username}))'

export FACTER_SMTP_SERVER='127.0.0.1'
export FACTER_SMTP_SERVER_PORT='25'
export FACTER_SMTP_USER=''
export FACTER_SMTP_PASS=''

puppet apply --modulepath modules/ gerrit_node.pp
