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

class mysql ($settings = hiera_hash('mysql', '')) {
    file { '/etc/monit/conf.d/mysql':
        ensure  => present,
        source  => 'puppet:///modules/mysql/monit',
        require => Package['monit'],
        notify  => Service['monit'],
    }
    
    service {'mysql':
        ensure     => running,
        enable     => true,
        hasrestart => true,
        hasstatus  => true,
    }
    
    file {'/root/create_databases.sql':
        ensure  => file,
        mode    => '0600',
        content => template('mysql/create_databases.sql.erb'),
    }
    
    exec {'create_databases':
        command     => "mysql -u root -pyour_password < /root/create_databases.sql",
        path        => '/usr/bin/:/bin/',
        refreshonly => true,
        subscribe   => File['/root/create_databases.sql'],
        require     => [Service['mysql'], File['/root/create_databases.sql']],
    }
}
