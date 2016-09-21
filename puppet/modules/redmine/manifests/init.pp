#
# Copyright (C) 2016 Red Hat
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

class redmine {
    include ::monit
    include ::apache

    $cauth_signin_url = "/auth/login"
    $cauth_signout_url = "/auth/logout"
    $theme = hiera('theme')
    $auth = hiera('authentication')
    $fqdn = hiera('fqdn')
    $url = hiera_hash('url')
    $sf_version = hiera('sf_version')
    $api_key = hiera('creds_issues_tracker_api_key')
    $mysql_url = "mysql.${fqdn}"
    $mysql_password = hiera('creds_redmine_sql_pwd')

    file { 'conf_yml':
      ensure  => file,
      path    => '/var/www/redmine/config/configuration.yml',
      mode    => '0640',
      owner   => 'apache',
      group   => 'apache',
      source  => 'puppet:///modules/redmine/configuration.yml',
    }

    file { 'dbconf_yml':
      ensure  => file,
      path    => '/var/www/redmine/config/database.yml',
      mode    => '0640',
      owner   => 'apache',
      group   => 'apache',
      content => template('redmine/database.erb'),
    }

    file {'/etc/httpd/conf.d/redmine.conf':
      ensure  => file,
      mode    => '0640',
      owner   => 'apache',
      group   => 'apache',
      content => template('redmine/redmine.site.erb'),
      notify  => Service['webserver'],
    }

    exec { 'chown_redmine':
      path    => '/usr/bin/:/bin/',
      command => "chown -R apache:apache /var/www/redmine",
      unless  => 'stat -c %U /var/www/redmine | grep apache',
    }

    file { '/root/post-conf-in-mysql.sql':
        ensure  => file,
        mode    => '0640',
        content => template('redmine/post-conf-in-mysql.sql.erb'),
        replace => true,
    }

    exec {'create_secret_token':
        environment => ['HOME=/root'],
        command     => 'bundle exec rake generate_secret_token',
        path        => '/usr/bin/:/bin/:/usr/local/bin',
        cwd         => '/var/www/redmine',
        require     => [File['dbconf_yml'],
                        File['conf_yml']],
        creates     => '/var/www/redmine/config/initializers/secret_token.rb',
        notify      => Exec['chown_redmine'],
    }

    exec {'create_db':
        environment => ['RAILS_ENV=production', 'HOME=/root'],
        command     => 'bundle exec rake db:migrate --trace',
        path        => '/usr/bin/:/bin/:/usr/local/bin',
        cwd         => '/var/www/redmine',
        require     => [Exec['create_secret_token']],
        unless      => 'bundle exec rake db:migrate:status | grep up',
        notify      => Exec['chown_redmine'],
    }

    exec {'default_data':
        environment => ['RAILS_ENV=production', 'REDMINE_LANG=en', 'HOME=/root'],
        command     => 'bundle exec rake redmine:load_default_data --trace > /var/www/redmine/defautl_data.log',
        path        => '/usr/bin/:/bin/:/usr/local/bin',
        cwd         => '/var/www/redmine',
        require     => [Exec['create_db']],
        creates     => '/var/www/redmine/defautl_data.log',
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

    file { '/etc/monit.d/redmine':
      ensure  => file,
      content => template('redmine/monit.erb'),
      notify  => Service['monit'],
    }

    exec {'plugin_install':
      environment => ['RAILS_ENV=production', 'REDMINE_LANG=en', 'HOME=/root'],
      command     => 'bundle exec rake redmine:plugins:migrate > /var/www/redmine/redmine_plugin_install.log',
      cwd         => '/var/www/redmine',
      path        => ['/bin', '/usr/bin', '/usr/local/bin'],
      require     => Exec['post-conf-in-mysql'],
      creates     => '/var/www/redmine/redmine_plugin_install.log',
      notify      => Exec['chown_redmine'],
    }

    exec {'redmine_backlog_install':
      environment =>  ['labels=false', 'story_trackers=Bug', 'task_tracker=Task', 'HOME=/root'],
      command     =>  'bundle exec rake redmine:backlogs:install RAILS_ENV=production',
      cwd         =>  '/var/www/redmine/',
      path        =>  ['/bin', '/usr/bin', '/usr/local/bin'],
      require     =>  Exec['create_db'],
      creates     => '/var/www/redmine/redmine_backlogs_install.log',
      notify      => Exec['chown_redmine'],
    }

    file {'/var/run/passenger':
      ensure => directory,
      mode   => '0644',
      owner  => 'apache',
      group  => 'apache',
    }

    file {'/var/run/passenger-instreg':
      ensure => directory,
      mode   => '0644',
      owner  => 'apache',
      group  => 'apache',
    }

    exec {'backlog_topmenu':
      command => "sed -i '/<head>/a <script src=\"/redmine/themes/classic/javascripts/theme.js\" type=\"text/javascript\"></script>' /var/www/redmine/plugins/redmine_backlogs/app/views/layouts/rb.html.erb",
      path    => '/usr/sbin/:/usr/bin/:/bin/',
      unless  => '/usr/bin/grep "javascripts/theme.js" /var/www/redmine/plugins/redmine_backlogs/app/views/layouts/rb.html.erb',
    }

  bup::scripts{ 'redmine_scripts':
    name           => 'redmine',
    backup_script  => 'redmine/backup.sh.erb',
    restore_script => 'redmine/restore.sh.erb',
  }
}
