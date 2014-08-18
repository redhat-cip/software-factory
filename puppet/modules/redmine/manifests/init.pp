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

    case $operatingsystem {
      centos: {
        $http = "httpd"
        $provider = "systemd"
        $httpd_user = "apache"
        $generate_session_store_cmd = 'bundle exec rake generate_session_store'
        $create_db_cmd = 'bundle exec rake db:migrate --trace'
        $default_data_cmd = 'bundle exec rake redmine:load_default_data --trace'
        $plugin_install_cmd = 'bundle exec rake redmine:plugins:migrate'
        $redmine_backlog_install_cmd = 'bundle exec rake redmine:backlogs:install RAILS_ENV=production'

        exec { 'chown_redmine':
          path    => '/usr/bin/:/bin/',
          command => "chown -R $httpd_user:$httpd_user /usr/share/redmine",
        }

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

      }
      debian: {
        $http = "apache2"
        $provider = "debian"
        $httpd_user = "www-data"
        $generate_session_store_cmd = 'rake generate_session_store'
        $create_db_cmd = 'rake db:migrate --trace'
        $default_data_cmd = 'rake redmine:load_default_data --trace'
        $plugin_install_cmd = 'rake redmine:plugins:migrate'
        $redmine_backlog_install_cmd = 'rake redmine:backlogs:install RAILS_ENV=production'

        package {'redmine':
          ensure => 'installed',
          name   => 'redmine',
        }

        package {'libapache2-mod-passenger':
          ensure => 'installed',
          name   => 'libapache2-mod-passenger',
        }

        file { 'conf_yml':
          path   => '/etc/redmine/default/configuration.yml',
          ensure  => file,
          mode    => '0640',
          owner  => $httpd_user,
          group  => $httpd_user,
          content => template('redmine/configuration.yml.erb'),
        }

        file { 'dbconf_yml':
          path   => '/etc/redmine/default/database.yml',
          ensure  => file,
          mode    => '0640',
          owner  => $httpd_user,
          group  => $httpd_user,
          content => template('redmine/database.erb'),
        }

        file { '/etc/apache2/sites-enabled/000-default':
          ensure => absent,
        }

        file {'/etc/apache2/mods-available/passenger.conf':
          ensure => file,
          mode   => '0640',
          owner  => $httpd_user,
          group  => $httpd_user,
          source =>'puppet:///modules/redmine/passenger.conf',
        }

        file {'/etc/apache2/sites-available/redmine':
          ensure => file,
          mode   => '0640',
          owner  => $httpd_user,
          group  => $httpd_user,
          content => template('redmine/redmine.site.erb'),
        }

        exec {'enable_redmine_site':
          command => 'a2ensite redmine',
          path    => '/usr/sbin/:/usr/bin/:/bin/',
          require => [File['/etc/apache2/sites-available/redmine'],
                      File['/etc/apache2/mods-available/passenger.conf']],
        }

        service {'webserver':
          name       => $http,
          ensure     => running,
          enable     => true,
          hasrestart => true,
          hasstatus  => true,
          require    => [Package[$http], Package['libapache2-mod-passenger']],
          subscribe  => [Exec['enable_redmine_site'],
                         Exec['redmine_backlog_install'],
                         Exec['plugin_install'],
                         Exec['set_url_root']],
        }

      }
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

    exec {'create_session_store':
        environment => ["HOME=/root"],
        command => $generate_session_store_cmd,
        path    => '/usr/bin/:/bin/:/usr/local/bin',
        cwd     => '/usr/share/redmine',
        require => [File['dbconf_yml'],
                    File['conf_yml']],
    }

    exec {'create_db':
        environment => ['RAILS_ENV=production', 'HOME=/root'],
        command     => $create_db_cmd,
        path        => '/usr/bin/:/bin/:/usr/local/bin',
        cwd         => '/usr/share/redmine',
        require     => [Exec['create_session_store']],
    }

    exec {'default_data':
        environment => ['RAILS_ENV=production', 'REDMINE_LANG=en', 'HOME=/root'],
        command     => $default_data_cmd,
        path        => '/usr/bin/:/bin/:/usr/local/bin',
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

    exec {'plugin_install':
      environment => ['RAILS_ENV=production', 'REDMINE_LANG=en', 'HOME=/root'],
      command     => $plugin_install_cmd,
      cwd         => '/usr/share/redmine',
      path        => ['/bin', '/usr/bin', '/usr/local/bin'],
      require     => Exec['post-conf-in-mysql'],
    }

    exec {'redmine_backlog_install':
      environment =>  ["story_trackers=Bug", "task_tracker=Task", 'HOME=/root'],
      command     =>  $redmine_backlog_install_cmd,
      cwd         =>  '/usr/share/redmine/',
      path        =>  ['/bin', '/usr/bin', '/usr/local/bin'],
      require     =>  Exec['create_db'],
    }

    exec {'set_url_root':
      command => "sed -i '/^.*::relative_url_root =.*/d' /usr/share/redmine/config/environment.rb && echo 'Redmine::Utils::relative_url_root = \"/redmine\"' >> /usr/share/redmine/config/environment.rb",
      path    => '/usr/sbin/:/usr/bin/:/bin/',
      require => Exec['default_data'],
    }
}
