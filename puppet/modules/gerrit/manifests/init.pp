# Install and maintain Gerrit Code Review.
# params:
#   canonicalweburl:
#     Used in the Gerrit config to generate links,
#       eg., https://review.example.com/
#   sshd_listen_address:
#   java_home:
#   email_private_key
#
class gerrit(
  $canonicalweburl = "http://${::fqdn}/",
  $sshd_listen_address = '*:29418',
  $email_private_key = '',
) {

  $java_home = '/usr/lib/jvm/java-7-openjdk-amd64/jre'

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

  # Prepare gerrit directories.  Even though some of these would be created
  # by the init command, we can go ahead and create them now and populate them.
  # That way the config files are already in place before init runs.

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

  # Gerrit sets these permissions in 'init'; don't fight them.
  # Template uses:
  # - $canonicalweburl
  # - $java_home
  # - $sshd_listen_address
  file { '/home/gerrit/site_path/etc/gerrit.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0644',
    content => template('gerrit/gerrit.config.erb'),
    replace => true,
    require => File['/home/gerrit/site_path/etc'],
  }

  # Secret files.
  # Gerrit sets these permissions in 'init'; don't fight them.  If
  # these permissions aren't set correctly, gerrit init will write a
  # new secure.config file and lose the mysql password.
  # Template uses $email_private_key
  file { '/home/gerrit/site_path/etc/secure.config':
    ensure  => present,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0600',
    content => template('gerrit/secure.config.erb'),
    replace => true,
    require => File['/home/gerrit/site_path/etc'],
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

  # If gerrit.war was just installed, run the Gerrit "init" command.
  exec { 'gerrit-initial-init':
    user      => 'gerrit',
    command   => '/usr/bin/java -jar /home/gerrit/gerrit.war init -d /home/gerrit/site_path --batch --no-auto-start',
    require   => [Package['openjdk-7-jre'],
                  User['gerrit'],
                  File['/home/gerrit/site_path/etc/gerrit.config'],
                  File['/home/gerrit/site_path/etc/secure.config']],
    notify    => Exec['gerrit-start'],
    logoutput => true,
  }

  # Symlink the init script.
  file { '/etc/init.d/gerrit':
    ensure  => link,
    target  => '/home/gerrit/site_path/bin/gerrit.sh',
    require => Exec['gerrit-initial-init'],
  }

  # The init script requires the path to gerrit to be set.
  file { '/etc/default/gerritcodereview':
    ensure  => present,
    content => 'GERRIT_SITE=/home/gerrit/site_path',
    replace => true,
    owner   => 'gerrit',
    group   => 'gerrit',
    mode    => '0444',
  }


  # Make sure the init script starts on boot.
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

}
