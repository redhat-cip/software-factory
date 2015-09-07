#!/bin/bash

# Copyright (C) 2015 eNovance SAS/Red Hat <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# kill the running mysql process
service mariadb stop

# start mysql in safe mode and skip grant tables
mysqld_safe --skip-grant-tables --skip-networking &

mysqldump -u root --opt --quote-names --skip-set-charset --default-character-set=latin1 redmine --result-file=/tmp/sf_redmine.sql

mysql -u root -e "ALTER DATABASE redmine CHARACTER SET utf8 COLLATE utf8_unicode_ci; ALTER TABLE users CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;"

mysql -u root --default-character-set=utf8 redmine < /tmp/sf_redmine.sql

rm /tmp/sf_redmine.sql

pkill -9 -f mysql

service mariadb start
