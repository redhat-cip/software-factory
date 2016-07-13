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

class gerrit {
  include ::monit
  include ::apache
  include ::gerrituser
  include ::ssh_keys_gerrit
  include ::bup
  include ::systemctl

  $fqdn = hiera('fqdn')
  $url = hiera('url')
  $settings = hiera('gerrit')
  $auth = hiera('authentication')

  $gerrit_email_pk = hiera('creds_gerrit_email_pk')
  $gerrit_token_pk = hiera('creds_gerrit_token_pk')
  $gerrit_local_key = hiera('creds_gerrit_local_sshkey')
  $gerrit_admin_key = hiera('creds_gerrit_admin_sshkey')
  $gerrit_service_rsa = hiera('gerrit_service_rsa')
  $gerrit_service_rsa_pub = hiera('gerrit_service_rsa_pub')
  $gerrit_admin_rsa = hiera('gerrit_admin_rsa')

  $gerrit_local_sshkey_rsa = hiera('creds_gerrit_local_sshkey')
  $gerrit_local_sshkey = "ssh-rsa ${gerrit_local_sshkey_rsa}"
  $gerrit_admin_sshkey_rsa = hiera('creds_gerrit_admin_sshkey')
  $gerrit_admin_sshkey = "ssh-rsa ${gerrit_admin_sshkey_rsa}"
  $gerrit_jenkins_sshkey_rsa = hiera('creds_jenkins_pub_key')
  $gerrit_jenkins_sshkey = "ssh-rsa ${gerrit_jenkins_sshkey_rsa}"

  $issues_tracker_api_url = $url['redmine_url']
  $issues_tracker_api_key = hiera('creds_issues_tracker_api_key')
  $gitweb_url = $url['gerrit_pub_url']

  $gerrit_admin_mail = "admin@${fqdn}"
  $provider = 'systemd'
  $gitweb_cgi = '/var/www/git/gitweb.cgi'

  $mysql_host = "mysql.${fqdn}"
  $mysql_port = 3306
  $mysql_user = 'gerrit'
  $mysql_password = hiera('creds_gerrit_sql_pwd')
  $mysql_db = 'gerrit'
  $service_user_password = hiera('creds_sf_service_user_pwd')

  file { 'gerrit_service':
    path    => '/lib/systemd/system/gerrit.service',
    owner   => 'gerrit',
    content => template('gerrit/gerrit.service.erb'),
    require => [Exec['gerrit-initial-init'],
                File['wait4mariadb']],
    notify  => Exec['systemctl_reload'],
  }

  file { '/var/www/git/gitweb.cgi':
    mode   => '0755',
  }

  # managesf uses gerrit_admin_key to ssh to gerrit
  # and update replication.config
  ssh_authorized_key { 'gerrit_admin_user':
    user    => 'gerrit',
    type    => 'ssh-rsa',
    key     => $gerrit_admin_key,
    require => File['/home/gerrit/.ssh'],
  }

  # Here we build the basic directory tree for Gerrit
  file { '/home/gerrit/site_path':
    ensure  => directory,
    owner   => 'gerrit',
    require => [User['gerrit'],
                Group['gerrit']],
  }
  file { '/home/gerrit/site_path/bin':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }
  file { '/home/gerrit/site_path/etc':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }
  file { '/home/gerrit/site_path/etc/mail':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path/etc'],
  }
  file { '/home/gerrit/site_path/hooks':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }
  file { '/home/gerrit/site_path/lib':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }
  file { '/home/gerrit/site_path/plugins':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }
  file { '/home/gerrit/site_path/static':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }
  file { '/home/gerrit/site_path/etc/ssh_host_rsa_key':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    content => inline_template('<%= @gerrit_service_rsa %>'),
    require => File['/home/gerrit/site_path/etc'],
  }
  file { '/home/gerrit/.ssh/id_rsa':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    content => inline_template('<%= @gerrit_service_rsa %>'),
    require => File['/home/gerrit/.ssh'],
  }
  file { '/home/gerrit/site_path/etc/ssh_host_rsa_key.pub':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    content => inline_template('<%= @gerrit_service_rsa_pub %>'),
    require => File['/home/gerrit/site_path/etc'],
  }
  file { '/home/gerrit/site_path/plugins/replication.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/replication.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  # Ensure the old versioned plugin is removed - needed by upgrade
  file { '/home/gerrit/site_path/plugins/reviewersbyblame-2.8.1.jar':
    ensure  => absent,
  }
  # Ensure the old named plugin is removed - needed by upgrade
  file { '/home/gerrit/site_path/plugins/gravatar.jar':
    ensure  => absent,
  }
  file { '/home/gerrit/site_path/plugins/reviewers-by-blame.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/reviewers-by-blame.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/avatars-gravatar.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/avatars-gravatar.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/delete-project.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/delete-project.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/download-commands.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/download-commands.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  # Version numbers are required by Gerrit for the following three .jars,
  # otherwise Gerrit downloads the file again
  # https://gerrit.googlesource.com/gerrit/+/v2.8.6.1/gerrit-pgm/src/main/resources/com/google/gerrit/pgm/libraries.config
  file { '/home/gerrit/site_path/lib/mysql-connector-java-5.1.21.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/mysql-connector-java.jar',
    require => File['/home/gerrit/site_path/lib'],
  }
  file { '/home/gerrit/site_path/lib/bcprov-jdk15on-151.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/bcprov.jar',
    require => File['/home/gerrit/site_path/lib'],
  }
  file { '/home/gerrit/site_path/lib/bcpkix-jdk15on-151.jar':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/bcpkix.jar',
    require => File['/home/gerrit/site_path/lib'],
  }
  file { '/home/gerrit/site_path/hooks/patchset-created':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0740',
    content => template('gerrit/patchset-created.erb'),
    require => File['/home/gerrit/site_path/hooks'],
  }
  file { '/home/gerrit/site_path/hooks/change-merged':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0740',
    content => template('gerrit/change-merged.erb'),
    require => File['/home/gerrit/site_path/hooks'],
  }
  file { '/home/gerrit/gerrit.war':
    ensure => file,
    owner  => 'gerrit',
    group  => 'gerrit',
    mode   => '0644',
    source => '/root/gerrit_data_source/gerrit.war',
  }

  # Here we setup file based on templates
  file { '/home/gerrit/site_path/etc/gerrit.config':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    content => template('gerrit/gerrit.config.erb'),
    require => File['/home/gerrit/site_path/etc'],
    replace => true,
  }
  file { '/home/gerrit/site_path/etc/secure.config':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    content => template('gerrit/secure.config.erb'),
    require => File['/home/gerrit/site_path/etc'],
    replace => true,
  }

  file {'/root/gerrit_admin_rsa':
    ensure  => file,
    mode    => '0400',
    owner   => 'root',
    group   => 'root',
    content => inline_template('<%= @gerrit_admin_rsa %>'),
  }
  file { '/root/gerrit_data_source/project.config':
    ensure => file,
    owner  => 'root',
    group  => 'root',
    mode   => '0640',
    source => 'puppet:///modules/gerrit/project.config',
  }
  file { '/root/gerrit_data_source/ssh_wrapper.sh':
    ensure => file,
    owner  => 'root',
    group  => 'root',
    mode   => '0740',
    source => 'puppet:///modules/gerrit/ssh_wrapper.sh',
    require => File['/root/gerrit_admin_rsa'],
  }
  file { '/root/gerrit-restore-user-keys.sql':
    ensure  => file,
    mode    => '0644',
    content => template('gerrit/gerrit-restore-user-keys.sql.erb'),
    replace => true,
  }
  file { '/root/gerrit-firstuser-init.sql':
    ensure  => file,
    mode    => '0644',
    content => template('gerrit/gerrit-firstuser-init.sql.erb'),
    replace => true,
    notify  => [Exec['gerrit-init-firstuser']],
  }
  file { '/root/gerrit-firstuser-init.sh':
    ensure  => file,
    mode    => '0700',
    content => template('gerrit/gerrit-firstuser-init.sh.erb'),
    replace => true,
  }
  file { '/root/gerrit-set-default-acl.sh':
    ensure  => file,
    mode    => '0700',
    content => template('gerrit/gerrit-set-default-acl.sh.erb'),
    replace => true,
  }
  file { '/root/gerrit-set-jenkins-user.sh':
    ensure  => file,
    mode    => '0700',
    content => template('gerrit/gerrit-set-jenkins-user.sh.erb'),
    replace => true,
    require => File['/root/gerrit_admin_rsa'],
  }

  file { 'wait4gerrit':
    path   => '/usr/libexec/wait4gerrit',
    mode   => '0755',
    owner  => 'root',
    group  => 'root',
    source => 'puppet:///modules/gerrit/wait4gerrit.sh',
  }

  # Gerrit first initialization, must be run only when gerrit.war changes
  exec { 'gerrit-initial-init':
    user        => 'gerrit',
    command     => '/usr/bin/java -jar /home/gerrit/gerrit.war init -d /home/gerrit/site_path --batch --no-auto-start',
    require     => [File['/home/gerrit/gerrit.war'],
                  File['/home/gerrit/site_path/plugins/replication.jar'],
                  File['/home/gerrit/site_path/plugins/avatars-gravatar.jar'],
                  File['/home/gerrit/site_path/plugins/delete-project.jar'],
                  File['/home/gerrit/site_path/plugins/reviewers-by-blame.jar'],
                  File['/home/gerrit/site_path/lib/mysql-connector-java-5.1.21.jar'],
                  File['/home/gerrit/site_path/lib/bcprov-jdk15on-151.jar'],
                  File['/home/gerrit/site_path/lib/bcpkix-jdk15on-151.jar'],
                  File['/home/gerrit/site_path/plugins/download-commands.jar'],
                  File['/home/gerrit/site_path/plugins/delete-project.jar'],
                  File['/home/gerrit/site_path/etc/gerrit.config'],
                  File['/home/gerrit/site_path/etc/secure.config'],
                  File['/root/gerrit-firstuser-init.sql'],
                  File['/root/gerrit-firstuser-init.sh'],
                  File['/root/gerrit-set-default-acl.sh'],
                  File['/root/gerrit-set-jenkins-user.sh']],
    subscribe   => File['/home/gerrit/gerrit.war'],
    refreshonly => true,
    logoutput   => on_failure,
  }

  # Gerrit reindex after first initialization
  exec { 'gerrit-reindex':
    user        => 'gerrit',
    command     => '/usr/bin/java -jar /home/gerrit/gerrit.war reindex -d /home/gerrit/site_path',
    require     => [Exec['gerrit-initial-init']],
    subscribe   => File['/home/gerrit/gerrit.war'],
    refreshonly => true,
    logoutput   => on_failure,
  }

  # Init default in Gerrit. Require a running gerrit but
  # must be done the first time after gerrit-init-init
  exec {'gerrit-init-firstuser':
    command     => '/root/gerrit-firstuser-init.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-initial-init'],
    require     => [Service['gerrit'],
                    File['/root/gerrit-firstuser-init.sql'],
                    File['/root/gerrit_admin_rsa']],
    refreshonly => true,
  }
  exec {'gerrit-init-acl':
    command     => '/root/gerrit-set-default-acl.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-init-firstuser'],
    require     => [Service['gerrit'],
                    File['/root/gerrit_data_source/project.config'],
                    File['/root/gerrit_data_source/ssh_wrapper.sh'],
                    File['/home/gerrit/gerrit.war']],
    refreshonly => true,
  }
  exec {'gerrit-init-jenkins':
    command     => '/root/gerrit-set-jenkins-user.sh',
    logoutput   => on_failure,
    subscribe   => [Exec['gerrit-init-firstuser'], File['/root/gerrit-set-jenkins-user.sh']],
    require     => Service['gerrit'],
    refreshonly => true,
  }

  # Gerrit process restart only when one of the configuration files
  # change or when gerrit-initial-init has been triggered
  service { 'gerrit':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    provider   => $provider,
    require    => [Exec['gerrit-initial-init'],
                    File['gerrit_service'],
                    Exec['systemctl_reload'],
                    File['/var/www/git/gitweb.cgi']],
    subscribe  => [File['/home/gerrit/gerrit.war'],
                    File['/home/gerrit/site_path/etc/gerrit.config'],
                    File['/root/gerrit-firstuser-init.sql'],
                    File['/home/gerrit/site_path/etc/secure.config']],
  }

  # Ensure mount point exists
  file { '/home/gerrit/site_path/git':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }

  # Install a default replication.config file
  file { '/home/gerrit/site_path/etc/replication.config':
    ensure  => file,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    source  => 'puppet:///modules/gerrit/replication.config',
    replace => false,
    require => File['/home/gerrit/site_path/etc'],
  }

  file { '/etc/monit.d/gerrit':
    ensure  => file,
    content => template('gerrit/monit.erb'),
    require => [Package['monit'], File['/etc/monit.d']],
    notify  => Service['monit'],
  }

  bup::scripts{ 'gerrit_scripts':
    name           => 'gerrit',
    backup_script  => 'gerrit/backup.sh.erb',
    restore_script => 'gerrit/restore.sh.erb',
  }

  file { '/home/gerrit/site_path/etc/GerritSiteHeader.html':
    ensure => file,
    owner  => 'gerrit',
    group  => 'gerrit',
    source => 'puppet:///modules/gerrit/GerritSiteHeader.html',
  }

}
