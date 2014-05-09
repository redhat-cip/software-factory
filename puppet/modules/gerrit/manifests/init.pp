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

class gerrit ($settings = hiera_hash('gerrit', '')) {

  # Here we just ensure that some basic stuff are present 
  package { 'openjdk-7-jre':
    ensure => present,
  }
  package { 'apache2':
    ensure => present,
  }
  user { 'gerrit':
    ensure => present,
    home => '/home/gerrit',
    system => true,
    managehome => true,
    comment => 'Gerrit sys user'
  }
  group { 'gerrit':
    ensure => present,
  }


  # Here we build the basic directory tree for Gerrit
  file { '/home/gerrit/site_path':
    ensure  => directory,
    owner   => 'gerrit',
    require => [User['gerrit'], Group['gerrit'],
                Package['openjdk-7-jre'],
                Package['apache2']],
  }
  file { '/home/gerrit/site_path/etc':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
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
    source  => '/root/gerrit_data_source/replication.jar',
    require => file['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/reviewersbyblame-2.8.1.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/reviewersbyblame-2.8.1.jar',
    require => file['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/gravatar.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/gravatar.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/delete-project.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/delete-project.jar',
    require => File['/home/gerrit/site_path/plugins'],
  }
  file { '/home/gerrit/site_path/plugins/download-commands.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/download-commands.jar',
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
  file { '/home/gerrit/site_path/lib/bcprov-jdk16-144.jar':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0640',
    source  => '/root/gerrit_data_source/bcprov-jdk16-144.jar',
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
  file { '/etc/default/gerritcodereview':
    ensure  => present,
    content => 'GERRIT_SITE=/home/gerrit/site_path',
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0444',
    require => File['/home/gerrit/site_path'],
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
  file { '/home/gerrit/site_path/etc/GerritSite.css':
    ensure  => file,
    mode    => '0644',
    owner   => 'root',
    group   => 'root',
    require => File['/home/gerrit/site_path/etc'],
    source  => 'puppet:///modules/gerrit/GerritSite.css'
  }
  file { '/home/gerrit/site_path/etc/GerritSiteHeader.html':
    ensure  => file,
    mode    => '0644',
    owner   => 'root',
    group   => 'root',
    require => File['/home/gerrit/site_path/etc'],
    source  => 'puppet:///modules/gerrit/GerritSiteHeader.html'
  }
  file { '/home/gerrit/site_path/static/logo.png':
    ensure  => file,
    mode    => '0644',
    owner   => 'root',
    group   => 'root',
    require => File['/home/gerrit/site_path/static'],
    source  => 'puppet:///modules/gerrit/logo.png'
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
  file { '/etc/apache2/sites-available/gerrit':
    ensure  => present,
    mode    => '0640',
    content => template('gerrit/apache_gerrit.erb'),
  }
  file { '/etc/apache2/sites-enabled/gerrit':
    ensure  => link,
    target  => '/etc/apache2/sites-available/gerrit',
    require => File['/etc/apache2/sites-available/gerrit'],
  }
  file { '/etc/apache2/sites-enabled/default':
    ensure  => absent,
  }
  file { '/etc/apache2/sites-enabled/000-default':
    ensure  => absent,
  }
  
  # Just to help debug
  exec { 'debug-copy-config-just-before-init':
    command   => "/bin/cp /home/gerrit/site_path/etc/*.config /tmp/",
    require => [File['/home/gerrit/site_path/etc/gerrit.config'],
                File['/home/gerrit/site_path/etc/secure.config']],
    logoutput => on_failure,
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
                  File['/home/gerrit/site_path/lib/bcprov-jdk16-144.jar'],
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

  exec { 'gerrit-change-start-timeout':
    command   => "/bin/sed -i 's/TIMEOUT=90/TIMEOUT=400/' /etc/init.d/gerrit",
    require   => File['/etc/init.d/gerrit'],
    logoutput => on_failure,
  }
  file { '/etc/init.d/gerrit':    
    ensure  => link,
    target  => '/home/gerrit/site_path/bin/gerrit.sh',
    require => Exec['gerrit-initial-init'],   
  }


  # Init default in Gerrit. Require a running gerrit but
  # must be done the first time after gerrit-init-init
  exec {'gerrit-init-firstuser':
    command     => '/root/gerrit-firstuser-init.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-initial-init'],
    require     => Service['gerrit'],
    refreshonly => true,
  }
  exec {'gerrit-init-acl':
    command     => '/root/gerrit-set-default-acl.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-init-firstuser'],
    require     => Service['gerrit'],
    refreshonly => true,
  }
  exec {'gerrit-init-jenkins':
    command     => '/root/gerrit-set-jenkins-user.sh',
    logoutput   => on_failure,
    subscribe   => Exec['gerrit-init-firstuser'],
    require     => Service['gerrit'],
    refreshonly => true,
  }
  # Just to help debug, we do a diff after the gerrit.war init
  exec { 'make-diff-config-after-init':
    cwd => '/tmp',
    path    => '/usr/bin/:/bin/',
    command   => "diff -rup gerrit.config /home/gerrit/site_path/etc/gerrit.config > /tmp/config.diff; diff -rup secure.config /home/gerrit/site_path/etc/secure.config >> /tmp/config.diff",
    logoutput => on_failure,
    subscribe   => Exec['gerrit-init-firstuser'],
    require     => Service['gerrit'],
    refreshonly => true,
  }


  # Gerrit process restart only when one of the configuration files
  # change or when gerrit-initial-init has been triggered
  service { 'gerrit':
    ensure      => running,
    enable      => true,
    hasrestart  => true,
    provider    => debian,
    require     => [Exec['gerrit-initial-init'],
    Exec['gerrit-change-start-timeout'],
    File['/etc/init.d/gerrit']],
    subscribe   => [File['/home/gerrit/gerrit.war'],
    File['/home/gerrit/site_path/etc/gerrit.config'],
    File['/home/gerrit/site_path/etc/secure.config']],
  }


  # Apache process restart only when one of the configuration files
  # change
  service { 'apache2':
    ensure      => running,
    enable      => true,
    hasrestart  => true,
    provider    => debian,
    require     => Service['gerrit'],
    subscribe   => [File['/etc/apache2/sites-enabled/gerrit'],
    File['/etc/apache2/sites-available/gerrit']],
  }

  # Create ext3 filesystem if the Cinder device is available
  exec { 'create_git_fs':
    path    => '/usr/bin:/usr/sbin:/bin',
    command => 'file -s /dev/vdb | grep -v ext3 && mkfs.ext3 /dev/vdb',
    onlyif => 'stat /dev/vdb',
  }

  # Ensure mount point exists
  file { '/home/gerrit/site_path/git':
    ensure => directory,
    owner => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }

  # To avoid failures we only create the mount entry in fstab
  # Otherwise the command will fail if there is no Cinder volume
  # which is ok if Cinder is missing
  mount { 'git_volume':
    name => '/home/gerrit/site_path/git/',
    ensure => 'present',
    atboot => 'false',
    device => '/dev/vdb',
    fstype => 'ext3',
    require => File['/home/gerrit/site_path/git'],
  }

  # Only mount if there is an ext3 on the device
  exec {'mount_git':
    path    => '/usr/bin:/usr/sbin:/bin',
    command => 'mount /home/gerrit/site_path/git/',
    onlyif => 'file -s /dev/vdb  | grep ext3',
    require => [Exec['create_git_fs'], Mount['git_volume']]
  }

  file { '/etc/monit/conf.d/gerrit':
    ensure  => present,
    content => template('gerrit/monit.erb'),
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

  file { '/etc/monit/conf.d/gerrit-fs':
    ensure  => present,
    source  => 'puppet:///modules/gerrit/monit-fs',
    require => [Package['monit'], Exec['mount_git'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

}
