scp -r puppet $1:.
ssh $1 "cd puppet ; FACTER_REDMINE_DATABASE_ADAPTER=mysql FACTER_REDMINE_DATABASE_NAME=redmine FACTER_REDMINE_DATABASE_HOST=localhost FACTER_REDMINE_DATABASE_USERNAME=root FACTER_REDMINE_DATABASE_PASSWORD=root puppet apply --modulepath modules/ redmine_node.pp"
