class gerrit {

  user { 'gerrit':
    ensure     => present,
    comment    => 'Gerrit',
    home       => '/home/gerrit',
    shell      => '/bin/bash',
    gid        => 'gerrit',
    managehome => true,
    require    => Group['gerrit'],
  }

  group { 'gerrit':
    ensure => present,
  }

  package { 'openjdk-7-jre':
    ensure => present,
  }

  file { '/home/gerrit/site_path':
    ensure  => directory,
    owner   => 'gerrit',
    require => User['gerrit'],
  }

  file { '/home/gerrit/site_path/etc':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }

  file { '/home/gerrit/site_path/bin':
    ensure  => directory,
    owner   => 'gerrit',
    require => File['/home/gerrit/site_path'],
  }

  file { '/home/gerrit/site_path/static':
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

  file { '/home/gerrit/site_path/etc/gerrit.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    content => template('gerrit/gerrit.config.erb'),
    replace => true,
    require => File['/home/gerrit/site_path/etc'],
  }

  file { '/home/gerrit/site_path/etc/secure.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    content => template('gerrit/secure.config.erb'),
    replace => true,
    require => File['/home/gerrit/site_path/etc'],
  }

  file { '/home/gerrit/gerrit.war':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    source  => '/root/gerrit_data_source/gerrit.war',
    replace => true,
  }

  if $ssh_dsa_key_contents != '' {
    file { '/home/gerrit/site_path/etc/ssh_host_dsa_key':
      owner   => 'gerrit',
      group   => 'gerrit',
      mode    => '0600',
      content => $ssh_dsa_key_contents,
      replace => true,
      require => File['/home/gerrit/site_path/etc']
    }
  }

  package { 'libmysql-java':
    ensure => present,
  }

  file { '/home/gerrit/site_path/lib/mysql-connector-java.jar':
    ensure  => link,
    target  => '/usr/share/java/mysql-connector-java-5.1.16.jar',
    require => [Package['libmysql-java'],
                File['/home/gerrit/site_path/lib']]  
  }

  exec { 'gerrit-initial-init':
    user      => 'gerrit',
    command   => '/usr/bin/java -jar /home/gerrit/gerrit.war init -d /home/gerrit/site_path --batch --no-auto-start',
    require   => [Package['openjdk-7-jre'],
                  User['gerrit'],
                  Group['gerrit'],
                  File['/home/gerrit/gerrit.war'],
                  File['/home/gerrit/site_path/etc/gerrit.config'],
                  File['/home/gerrit/site_path/etc/secure.config']],
    unless    => '/usr/bin/pgrep -f GerritCodeReview',
    notify    => Exec['gerrit-start'],
    logoutput => true,
  }

  file { '/etc/init.d/gerrit':
    ensure  => link,
    target  => '/home/gerrit/site_path/bin/gerrit.sh',
    require => Exec['gerrit-initial-init'],
  }

  file { '/etc/default/gerritcodereview':
    ensure  => present,
    content => 'GERRIT_SITE=/home/gerrit/site_path',
    replace => true,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0444',
  }

  file { ['/etc/rc0.d/K10gerrit',
          '/etc/rc1.d/K10gerrit',
          '/etc/rc2.d/S90gerrit',
          '/etc/rc3.d/S90gerrit',
          '/etc/rc4.d/S90gerrit',
          '/etc/rc5.d/S90gerrit',
          '/etc/rc6.d/K10gerrit']:
    ensure  => link,
    target  => '/etc/init.d/gerrit',
    require => File['/etc/init.d/gerrit'],
  }

  exec { 'gerrit-start':
    command     => '/etc/init.d/gerrit start',
    require     => File['/etc/init.d/gerrit'],
    refreshonly => true,
  }
  
  exec { 'gerrit-restart':
    command     => '/etc/init.d/gerrit restart',
    require     => File['/etc/init.d/gerrit'],
    onlyif      => '/usr/bin/test -f /home/gerrit/site_path/bin/gerrit.sh',
    subscribe   => [File['/home/gerrit/site_path/etc/gerrit.config'],
                    File['/home/gerrit/site_path/etc/secure.config']],
    refreshonly => true,
  }

}
