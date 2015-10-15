#
class lodgeit {

  require hosts
  include ::apache

  $fqdn = hiera('fqdn')
  $session_key = hiera('creds_lodgeit_session_key')
  $mysql_db_address = "mysql.${fqdn}"
  $mysql_db_secret = hiera('creds_lodgeit_sql_pwd')
  $mysql_db_username = 'lodgeit'
  $mysql_db = 'lodgeit'

  file {'init':
    ensure  => file,
    path    => '/lib/systemd/system/lodgeit.service',
    mode    => '0755',
    source  => 'puppet:///modules/lodgeit/lodgeit.service',
    require => File['/srv/lodgeit/lodgeit/manage.py'],
  }

  file { '/srv/lodgeit/lodgeit/manage.py':
    ensure  => file,
    mode    => '0755',
    replace => true,
    owner   => $::httpd_user,
    group   => $::httpd_user,
    content => template('lodgeit/manage.py.erb'),
    notify  => Service['lodgeit'],
  }

  file { '/srv/lodgeit/lodgeit/lodgeit/urls.py':
    ensure  => file,
    mode    => '0755',
    replace => true,
    owner   => $::httpd_user,
    group   => $::httpd_user,
    source  => 'puppet:///modules/lodgeit/urls.py',
    notify  => Service['lodgeit'],
  }

  service {'lodgeit':
    ensure    => running,
    enable    => true,
    hasstatus => true,
    require   => [File['init'],
        File['/srv/lodgeit/lodgeit/manage.py'],
        File['/srv/lodgeit/lodgeit/lodgeit/urls.py']],
  }

  file { '/var/www/static/lodgeit':
    ensure => link,
    target => '/srv/lodgeit/lodgeit/lodgeit/static/',
  }
}
