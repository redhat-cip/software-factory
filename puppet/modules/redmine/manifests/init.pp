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

class redmine ($settings = hiera_hash('redmine', ''),
               $cauth = hiera_hash('cauth', '')) {

    $mysql_url = $settings['redmine_mysql_db_address']
    $mysql_password = $settings['redmine_mysql_db_secret']

    require cauth_client

    $http = "httpd"
    $provider = "systemd"
    $httpd_user = "apache"

    file { 'conf_yml':
      path   => '/usr/share/redmine/config/configuration.yml',
      ensure  => file,
      mode    => '0640',
      owner  => $httpd_user,
      group  => $httpd_user,
      content => template('redmine/configuration.yml.erb'),
    }

    file { 'dbconf_yml':
      path    => '/usr/share/redmine/config/database.yml',
      ensure  => file,
      mode    => '0640',
      owner  => $httpd_user,
      group  => $httpd_user,
      content => template('redmine/database.erb'),
    }

    file {'/etc/httpd/conf.modules.d/passenger.conf':
      ensure => file,
      mode   => '0640',
      owner  => $httpd_user,
      group  => $httpd_user,
      source =>'puppet:///modules/redmine/centos_passenger.conf',
    }

    file {'/etc/httpd/conf.d/redmine.conf':
      ensure => file,
      mode   => '0640',
      owner  => $httpd_user,
      group  => $httpd_user,
      content => template('redmine/redmine.site.erb'),
    }

    service {'webserver':
      name       => $http,
      ensure     => running,
      enable     => true,
      hasrestart => true,
      hasstatus  => true,
      subscribe  => [File['/etc/httpd/conf.d/redmine.conf'],
                     File['/etc/httpd/conf.modules.d/passenger.conf'],
                     Exec['redmine_backlog_install'],
                     Exec['plugin_install'],
                     Exec['set_url_root']],
      require => Exec['chown_redmine'],
    }

    exec { 'chown_redmine':
      path    => '/usr/bin/:/bin/',
      command => "chown -R $httpd_user:$httpd_user /usr/share/redmine",
      unless  => 'stat -c %U /usr/share/redmine | grep apache'
    }

    package { $http:
        ensure => 'installed',
    }

    file { '/root/post-conf-in-mysql.sql':
        ensure  => present,
        mode    => '0640',
        content => template('redmine/post-conf-in-mysql.sql.erb'),
        replace => true,
    }

    exec {'create_secret_token':
        environment => ["HOME=/root"],
        command => 'bundle exec rake generate_secret_token',
        path    => '/usr/bin/:/bin/:/usr/local/bin',
        cwd     => '/usr/share/redmine',
        require => [File['dbconf_yml'],
                    File['conf_yml']],
        creates => "/usr/share/redmine/config/initializers/secret_token.rb",
        notify      => Exec['chown_redmine'],
    }

    exec {'create_db':
        environment => ['RAILS_ENV=production', 'HOME=/root'],
        command     => 'bundle exec rake db:migrate --trace',
        path        => '/usr/bin/:/bin/:/usr/local/bin',
        cwd         => '/usr/share/redmine',
        require     => [Exec['create_secret_token']],
        unless      => 'bundle exec rake db:migrate:status | grep up',
        notify      => Exec['chown_redmine'],
    }

    exec {'default_data':
        environment => ['RAILS_ENV=production', 'REDMINE_LANG=en', 'HOME=/root'],
        command     => 'bundle exec rake redmine:load_default_data --trace > /usr/share/redmine/defautl_data.log',
        path        => '/usr/bin/:/bin/:/usr/local/bin',
        cwd         => '/usr/share/redmine',
        require     => [Exec['create_db']],
        creates     => "/usr/share/redmine/defautl_data.log",
        notify      => Exec['chown_redmine'],
    }

    exec {'post-conf-in-mysql':
        command     => "mysql -u redmine redmine -p\"${mysql_password}\" -h ${mysql_url} < /root/post-conf-in-mysql.sql",
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/bin',
        refreshonly => true,
        subscribe   => File['/root/post-conf-in-mysql.sql'],
        require     => [Exec['default_data']],
        notify      => Exec['chown_redmine'],
    }

    file { '/etc/monit/conf.d/redmine':
      ensure  => present,
      content => template('redmine/monit.erb'),
      require => [Package['monit'], File['/etc/monit/conf.d']],
      notify  => Service['monit'],
    }

    exec {'plugin_install':
      environment => ['RAILS_ENV=production', 'REDMINE_LANG=en', 'HOME=/root'],
      command     => 'bundle exec rake redmine:plugins:migrate > /usr/share/redmine/redmine_plugin_install.log',
      cwd         => '/usr/share/redmine',
      path        => ['/bin', '/usr/bin', '/usr/local/bin'],
      require     => Exec['post-conf-in-mysql'],
      creates     => '/usr/share/redmine/redmine_plugin_install.log',
      notify      => Exec['chown_redmine'],
    }

    exec {'redmine_backlog_install':
      environment =>  ["labels=false", "story_trackers=Bug", "task_tracker=Task", 'HOME=/root'],
      command     =>  'bundle exec rake redmine:backlogs:install RAILS_ENV=production',
      cwd         =>  '/usr/share/redmine/',
      path        =>  ['/bin', '/usr/bin', '/usr/local/bin'],
      require     =>  Exec['create_db'],
      creates     => '/usr/share/redmine/redmine_backlogs_install.log',
      notify      => Exec['chown_redmine'],
    }

    exec {'set_url_root':
      command => "sed -i '/^.*::relative_url_root =.*/d' /usr/share/redmine/config/environment.rb && echo 'Redmine::Utils::relative_url_root = \"/redmine\"' >> /usr/share/redmine/config/environment.rb",
      path    => '/usr/sbin/:/usr/bin/:/bin/',
      require => Exec['default_data'],
      unless  => '/usr/bin/grep "relative_url_root = \"/redmine\"" /usr/share/redmine/config/environment.rb',
      notify      => Exec['chown_redmine'],
    }
}
