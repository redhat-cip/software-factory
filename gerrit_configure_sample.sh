#scp -r puppet $1:.
#ssh $1 "cd puppet ; FACTER_REDMINE_DATABASE_ADAPTER=mysql FACTER_REDMINE_DATABASE_NAME=redmine FACTER_REDMINE_DATABASE_HOST=localhost FACTER_REDMINE_DATABASE_USERNAME=root FACTER_REDMINE_DATABASE_PASSWORD=root puppet apply --modulepath modules/ redmine_node.pp"

cd puppet

# Where repo are store in the FS
#export FACTER_REPO_BASE_PATH="git"

# Gerrit WEB UI address
export FACTER_WEBURL="http://198.154.188.164:8080"

# Can be use to set HTTP read access from a mirror
#export FACTER_HTTPURL="http://mirror.monrepo.local"

# Bug tracker URL
#export FACTER_REPORTBUGURL="http://redmine.monrepo.local"

# Binding address for sshd
#export FACTER_SSHD_LISTEN_ADDRESS="*:29418"

# Binding address for httpd
#export FACTER_HTTP_LISTEN_ADDRESS="http://*:8080"

# MySQL access
export FACTER_MYSQL_ADDRESS="10.43.0.37"
#export FACTER_GERRIT_MYSQL_DB="gerrit"
#export FACTER_GERRIT_MYSQL_USERNAME="gerrit"
#export FACTER_MYSQL_POST="3306"
export FACTER_GERRIT_MYSQL_SECRET="secret"

export FACTER_LDAP_ADDRESS="ldap://10.43.0.61"
export FACTER_LDAP_USERNAME="cn=admin,dc=enovance,dc=com"
export FACTER_LDAP_PASSWORD="secret"
export FACTER_LDAP_ACCOUNT_BASE="ou=Users,dc=enovance,dc=com"
export FACTER_LDAP_ACCOUNT_PATTERN='(&(objectClass=inetOrgPerson)(cn=${username}))'
export FACTER_LDAP_ACCOUNT_EMAIL_ADDRESS='mail'
export FACTER_LDAP_ACCOUNT_SSH_USERNAME='cn'

# Authenticated HTTP access use LDAP backend
export FACTER_HTTP_BASIC_AUTH='true'

export FACTER_SMTP_SERVER='smtp.enovance.com'
#export FACTER_SMTP_SERVER_PORT='25'
#export FACTER_SMTP_USER=''
#export FACTER_SMTP_PASS=''

puppet apply --modulepath modules/ gerrit_node.pp
