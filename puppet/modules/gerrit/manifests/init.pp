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

class gerrit ($settings = hiera_hash('gerrit', ''),
              $cauth = hiera_hash('cauth', '')) {

  require hosts

  $http = "httpd"
  $provider = "systemd"
  $httpd_user = "apache"
  $gitweb_cgi = "/var/www/git/gitweb.cgi"

  file { '/etc/httpd/conf.d/gerrit.conf':
    ensure  => present,
    mode    => '0640',
    content => template('gerrit/apache_gerrit.erb'),
  }

  file { 'gerrit_init':
    path  => '/lib/systemd/system/gerrit.service',
    owner => 'gerrit',
    content => template('gerrit/gerrit.service.erb'),
    require => Exec['gerrit-initial-init'],
  }

  # Apache process restart only when one of the configuration files change
  service { 'webserver':
    name        => $http,
    ensure      => running,
    enable      => true,
    hasrestart  => true,
    provider    => $provider,
    require     => Service['gerrit'],
    subscribe   => File['/etc/httpd/conf.d/gerrit.conf'],
  }

  package { $http:
    ensure => present,
  }

  group { 'gerrit':
    ensure => present,
  }
  user { 'gerrit':
    ensure => present,
    home => '/home/gerrit',
    system => true,
    managehome => true,
    comment => 'Gerrit sys user',
    require => Group['gerrit'],
  }

  file { '/home/gerrit/.ssh':
    ensure  => directory,
    owner   => 'gerrit',
    require => [User['gerrit'], Group['gerrit']],
  }
  file { '/home/gerrit/.ssh/config':
    ensure  => present,
    content => template('gerrit/ssh_config.erb'),
    mode    => '0644',
    owner  => 'gerrit',
    group  => 'gerrit',
    require => File['/home/gerrit/.ssh'],
  }
#managesf uses gerrit_admin_key to ssh to gerrit
# and update replication.config
  ssh_authorized_key { 'gerrit_admin_user':
    user => 'gerrit',
    type => 'rsa',
    key  => $settings['gerrit_admin_key'],
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
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    source  => 'puppet:///modules/gerrit/gerrit_service_rsa',
    require => File['/home/gerrit/site_path/etc'],
  }
  file { '/home/gerrit/site_path/etc/ssh_host_rsa_key.pub':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    source  => 'puppet:///modules/gerrit/gerrit_service_rsa.pub',
    require => File['/home/gerrit/site_path/etc'],
  }
  file { '/home/gerrit/site_path/plugins/replication.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/replication.jar',
    require => file['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/reviewersbyblame-2.8.1.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/reviewersbyblame-2.8.1.jar',
    require => file['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/gravatar.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/gravatar.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/delete-project.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/delete-project.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/download-commands.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/download-commands.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/lib/mysql-connector-java-5.1.21.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/mysql-connector-java-5.1.21.jar',
    require => File['/home/gerrit/site_path/lib'],
  }
  file { '/home/gerrit/site_path/lib/bcprov-jdk15on-149.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/bcprov-jdk15on-149.jar',
    require => File['/home/gerrit/site_path/lib'],
  }
  file { '/home/gerrit/site_path/lib/bcpkix-jdk15on-149.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/bcpkix-jdk15on-149.jar',
    require => File['/home/gerrit/site_path/lib'],
  }
  file { '/home/gerrit/site_path/hooks/patchset-created':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0740',
    source  => '/root/gerrit_data_source/gerrit-hooks/patchset-created',
    require => File['/home/gerrit/site_path/hooks'],
  }
  file { '/home/gerrit/site_path/hooks/change-merged':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0740',
    source  => '/root/gerrit_data_source/gerrit-hooks/change-merged',
    require => File['/home/gerrit/site_path/hooks'],
  }
  file { '/home/gerrit/gerrit.war':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    source  => '/root/gerrit_data_source/gerrit.war',
  }
  file { '/home/gerrit/site_path/etc/mail/RegisterNewEmail.vm':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/RegisterNewEmail.vm',
    require => file['/home/gerrit/site_path/etc/mail'],
  }

  # Here we setup file based on templates
  file { '/home/gerrit/site_path/etc/gerrit.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    content => template('gerrit/gerrit.config.erb'),
    require => File['/home/gerrit/site_path/etc'],
    replace => true,
  }
  file { '/home/gerrit/site_path/etc/secure.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    content => template('gerrit/secure.config.erb'),
    require => File['/home/gerrit/site_path/etc'],
    replace => true,
  }
  file { '/home/gerrit/site_path/hooks/hooks.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    content => template('gerrit/hooks.config.erb'),
    require => File['/home/gerrit/site_path/hooks'],
    replace => true,
  }
  file { '/root/gerrit_data_source/project.config':
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/project.config',
  }
  file { '/root/gerrit_data_source/rules.pl':
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0640',
    source  => 'puppet:///modules/gerrit/rules.pl',
  }
  file { '/root/gerrit_data_source/ssh_wrapper.sh':
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0740',
    source  => 'puppet:///modules/gerrit/ssh_wrapper.sh',
  }
  file { '/root/gerrit-restore-user-keys.sql':
    ensure  => present,
    mode    => '0644',
    content => template('gerrit/gerrit-restore-user-keys.sql.erb'),
    replace => true,
  }
  file { '/root/gerrit-firstuser-init.sql':
    ensure  => present,
    mode    => '0644',
    content => template('gerrit/gerrit-firstuser-init.sql.erb'),
    replace => true,
  }
  file { '/root/gerrit-firstuser-init.sh':
    ensure  => present,
    mode    => '0700',
    content => template('gerrit/gerrit-firstuser-init.sh.erb'),
    replace => true,
  }
  file { '/root/gerrit-set-default-acl.sh':
    ensure  => present,
    mode    => '0700',
    content => template('gerrit/gerrit-set-default-acl.sh.erb'),
    replace => true,
  }
  file { '/root/gerrit-set-jenkins-user.sh':
    ensure  => present,
    mode    => '0700',
    content => template('gerrit/gerrit-set-jenkins-user.sh.erb'),
    replace => true,
  }

  file { 'wait4gerrit':
    path    => '/root/wait4gerrit.sh',
    mode    => '0740',
    source  => 'puppet:///modules/gerrit/wait4gerrit.sh',
  }

  # Just to help debug
  exec { 'debug-copy-config-just-before-init':
    command   => "/bin/cp /home/gerrit/site_path/etc/*.config /tmp/",
    require => [File['/home/gerrit/site_path/etc/gerrit.config'],
                File['/home/gerrit/site_path/etc/secure.config']],
    logoutput => on_failure,
    creates => '/tmp/gerrit.config'
  }


  # Gerrit first initialization, must be run only when gerrit.war changes
  exec { 'gerrit-initial-init':
    user      => 'gerrit',
    command   => '/usr/bin/java -jar /home/gerrit/gerrit.war init -d /home/gerrit/site_path --batch --no-auto-start',
    require   => [File['/home/gerrit/gerrit.war'],
                  File['/home/gerrit/site_path/plugins/replication.jar'],
                  File['/home/gerrit/site_path/plugins/gravatar.jar'],
                  File['/home/gerrit/site_path/plugins/delete-project.jar'],
                  File['/home/gerrit/site_path/plugins/reviewersbyblame-2.8.1.jar'],
                  File['/home/gerrit/site_path/lib/mysql-connector-java-5.1.21.jar'],
                  File['/home/gerrit/site_path/lib/bcprov-jdk15on-149.jar'],
                  File['/home/gerrit/site_path/lib/bcpkix-jdk15on-149.jar'],
                  File['/home/gerrit/site_path/plugins/download-commands.jar'],
                  File['/home/gerrit/site_path/plugins/delete-project.jar'],
                  File['/home/gerrit/site_path/hooks/hooks.config'],
                  File['/home/gerrit/site_path/etc/gerrit.config'],
                  File['/home/gerrit/site_path/etc/secure.config'],
                  File['/root/gerrit-firstuser-init.sql'],
                  File['/root/gerrit-firstuser-init.sh'],
                  File['/root/gerrit-set-default-acl.sh'],
                  File['/root/gerrit-set-jenkins-user.sh'],
                  Exec['debug-copy-config-just-before-init']],
    subscribe => File['/home/gerrit/gerrit.war'],
    refreshonly => true,
    logoutput => on_failure,
  }

  # This ressource wait for gerrit TCP ports are up
  # Be really tolenrant with the timeout Gerrit can take long
  # to start in, it seems, low mem env ...
  exec { 'wait4gerrit':
    path    => '/usr/bin:/usr/sbin:/bin',
    command => '/root/wait4gerrit.sh',
    timeout => 900,
    require => [File['wait4gerrit'],  Service['gerrit']],
    creates => '/tmp/wait4gerrit.done',
  }

  # Init default in Gerrit. Require a running gerrit but
  # must be done the first time after gerrit-init-init
  exec {'gerrit-init-firstuser':
    command     => '/root/gerrit-firstuser-init.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-initial-init'],
    require     => [Service['gerrit'], Exec['wait4gerrit']],
    refreshonly => true,
  }
  exec {'gerrit-init-acl':
    command     => '/root/gerrit-set-default-acl.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-init-firstuser'],
    require     => [Service['gerrit'], Exec['wait4gerrit'],
                    File['/root/gerrit_data_source/rules.pl'],
                    File['/root/gerrit_data_source/project.config'],
                    File['/root/gerrit_data_source/ssh_wrapper.sh']],
    refreshonly => true,
  }
  exec {'gerrit-init-jenkins':
    command     => '/root/gerrit-set-jenkins-user.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-init-firstuser'],
    require     => [Service['gerrit'], Exec['wait4gerrit']],
    refreshonly => true,
  }
  # Just to help debug, we do a diff after the gerrit.war init
  exec { 'make-diff-config-after-init':
    cwd => '/tmp',
    path    => '/usr/bin/:/bin/',
    command   => "diff -rup gerrit.config /home/gerrit/site_path/etc/gerrit.config > /tmp/config.diff; diff -rup secure.config /home/gerrit/site_path/etc/secure.config >> /tmp/config.diff",
    logoutput => on_failure,
    subscribe   => Exec['gerrit-init-firstuser'],
    require     => [Service['gerrit'], Exec['wait4gerrit']],
    refreshonly => true,
  }


  # Gerrit process restart only when one of the configuration files
  # change or when gerrit-initial-init has been triggered
  service { 'gerrit':
    ensure      => running,
    enable      => true,
    hasrestart  => true,
    provider    => $provider,
    require     => [Exec['gerrit-initial-init'],
                    File['gerrit_init']],
    subscribe   => [File['/home/gerrit/gerrit.war'],
                    File['/home/gerrit/site_path/etc/gerrit.config'],
                    File['/home/gerrit/site_path/etc/secure.config']],
  }

#  # Create ext3 filesystem if the Cinder device is available
#  exec { 'create_git_fs':
#    path    => '/usr/bin:/usr/sbin:/bin',
#    command => 'file -s /dev/vdb | grep -v ext3 && mkfs.ext3 /dev/vdb',
#    onlyif => 'stat /dev/vdb',
#  }

  # Ensure mount point exists
  file { '/home/gerrit/site_path/git':
    ensure => directory,
    owner => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }

#  # To avoid failures we only create the mount entry in fstab
#  # Otherwise the command will fail if there is no Cinder volume
#  # which is ok if Cinder is missing
#  mount { 'git_volume':
#    name => '/home/gerrit/site_path/git/',
#    ensure => 'present',
#    atboot => 'false',
#    device => '/dev/vdb',
#    fstype => 'ext3',
#    require => File['/home/gerrit/site_path/git'],
#  }
#
#  # Only mount if there is an ext3 on the device
#  exec {'mount_git':
#    path    => '/usr/bin:/usr/sbin:/bin',
#    command => 'mount /home/gerrit/site_path/git/',
#    onlyif => 'file -s /dev/vdb  | grep ext3',
#    require => [Exec['create_git_fs'], Mount['git_volume']]
#  }

  file { '/etc/monit/conf.d/gerrit':
    ensure  => present,
    content => template('gerrit/monit.erb'),
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

  file { '/etc/monit/conf.d/gerrit-fs':
    ensure  => present,
    source  => 'puppet:///modules/gerrit/monit-fs',
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

  #Create an empty file, later this file is configured with init-config-repo
  file { '/home/gerrit/site_path/etc/replication.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    require => File['/home/gerrit/site_path/etc'],
  }
  bup::scripts{ 'gerrit_scripts':
    backup_script => 'gerrit/backup.sh.erb',
    restore_script => 'gerrit/restore.sh.erb',
  }
}
