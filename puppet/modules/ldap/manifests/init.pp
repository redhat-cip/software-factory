#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

class ldap () {
    package {'cron':
        ensure => 'installed',
        name   => 'cron',
    }

    file {'/root/ldapdump.sh':
        ensure  => file,
        mode    => '700',
        content => template('ldap/ldapdump.sh'),
        require => [Package['cron']],
    }

    file {'/var/spool/cron/crontabs/root':
        ensure => file,
        mode   => '600',
        content => '0 * * * * bash /root/ldapdump.sh
',
        require => [File['/root/ldapdump.sh']]
    }

    file { '/etc/monit/conf.d/ldap':
        ensure  => present,
        source  => 'puppet:///modules/ldap/monit',
        require => [Package['monit'], File['/etc/monit/conf.d']],
        notify  => Service['monit'],
    }

}
