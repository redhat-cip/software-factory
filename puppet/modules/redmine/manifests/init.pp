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

class redmine ($settings = hiera_hash('redmine', ''),$ldap_sync_settings = hiera_hash('redmine_ldap_setting', '')) {

    $mysql_url = $settings['redmine_mysql_db_address']
    $mysql_password = $settings['redmine_mysql_db_secret']

    package {'redmine':
        ensure => 'installed',
        name   => 'redmine',
    }

    package {'apache2':
        ensure => 'installed',
        name   => 'apache2',
    }

    package {'libapache2-mod-passenger':
        ensure => 'installed',
        name   => 'libapache2-mod-passenger',
    }

    service {'apache2':
        ensure     => running,
        enable     => true,
        hasrestart => true,
        hasstatus  => true,
        require    => [Package['apache2'], Package['libapache2-mod-passenger']],
    }

    file {'/etc/redmine/default/database.yml':
        ensure  => file,
        mode    => '0640',
        owner   => 'www-data',
        group   => 'www-data',
        content => template('redmine/database.erb'),
    }

    file {'/etc/redmine/default/configuration.yml':
        ensure  => file,
        mode    => '0640',
        owner   => 'www-data',
        group   => 'www-data',
        content => template('redmine/configuration.yml.erb'),
    }

    file {'/etc/apache2/mods-available/passenger.conf':
        ensure => file,
        mode   => '0640',
        owner  => 'www-data',
        group  => 'www-data',
        source =>'puppet:///modules/redmine/passenger.conf',
        notify => Service[apache2],
    }

    file {'/etc/apache2/sites-available/redmine':
        ensure => file,
        mode   => '0640',
        owner  => 'www-data',
        group  => 'www-data',
        source =>'puppet:///modules/redmine/redmine',
        notify => Service[apache2],
    }

    file { '/etc/apache2/sites-enabled/000-default':
        ensure => absent,
    }
  
    file { '/root/post-conf-in-mysql.sql':
        ensure  => present,
        mode    => '0640',
        content => template('redmine/post-conf-in-mysql.sql.erb'),
        replace => true,
    }

    exec {'enable_redmine_site':
        command => 'a2ensite redmine',
        path    => '/usr/sbin/:/usr/bin/:/bin/',
        require => [File['/etc/apache2/sites-available/redmine']],
        before  => Class['monit'],
    }

    exec {'create_session_store':
        command => 'rake generate_session_store',
        path    => '/usr/bin/:/bin/',
        cwd     => '/usr/share/redmine',
        require => [File['/etc/redmine/default/database.yml']],
    }

    exec {'create_db':
        environment => ['RAILS_ENV=production'],
        command     => 'rake db:migrate --trace',
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/share/redmine',
        require     => [Exec['create_session_store']],
    }

    exec {'default_data':
        environment => ['RAILS_ENV=production', 'REDMINE_LANG=en'],
        command     => 'rake redmine:load_default_data --trace',
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/share/redmine',
        require     => [Exec['create_db']],
    }

    exec {'post-conf-in-mysql':
        command     => "mysql -u redmine redmine -p\"${mysql_password}\" -h ${mysql_url} < /root/post-conf-in-mysql.sql",
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/bin',
        refreshonly => true,
        subscribe   => File['/root/post-conf-in-mysql.sql'],
        require     => [Exec['default_data']],
    }

  file { '/etc/monit/conf.d/redmine':
    ensure  => present,
    content => template('redmine/monit.erb'),
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

  file { '/usr/share/redmine/public/plugin_assets':
    ensure  => directory,
    require => [Package['redmine'], Exec['post-conf-in-mysql']],
  }

  file { '/usr/share/redmine/public/plugin_assets/redmine_ldap_sync':
    ensure  => link,
    target  => '/usr/share/redmine/plugins/redmine_ldap_sync/assets',
    require => File['/usr/share/redmine/public/plugin_assets'],
  }

  exec {'plugin_install':
    environment => ['RAILS_ENV=production', 'REDMINE_LANG=en'],
    command     => 'rake redmine:plugins:migrate',
    cwd => '/usr/share/redmine',
    path => ['/bin', '/usr/bin'],
    require => File['/usr/share/redmine/public/plugin_assets/redmine_ldap_sync'],
  }

  exec {'ldap_sync_users':
    environment => ['RAILS_ENV=production', 'REDMINE_LANG=en'],
    command     => 'rake redmine:plugins:ldap_sync:sync_users',
    cwd => '/usr/share/redmine',
    path => ['/bin', '/usr/bin'],
    require => Exec['plugin_install'],
  }

  exec {'rake redmine:backlogs:install RAILS_ENV=production' :
    cwd         =>  '/usr/share/redmine/plugins/redmine_backlogs',
    path        =>  ['/bin', '/usr/bin'],
    environment =>  ["story_trackers=Bug", "task_tracker=Task"],
    require     =>  Exec['create_db'],
  }

  file { '/root/configure-admin-user.sql':
    ensure  => present,
    mode    => '0640',
    content => template('redmine/configure-admin-user.sql.erb'),
    replace => true,
  }

  exec {'configure-admin-user':
    command     => "mysql -u redmine redmine -p\"${mysql_password}\" -h ${mysql_url} < /root/configure-admin-user.sql",
    path        => '/usr/bin/:/bin/',
    cwd         => '/usr/bin',
    refreshonly => true,
    subscribe   => File['/root/configure-admin-user.sql'],
    require     => Exec['ldap_sync_users'],
  }

}
