class lodgeit ($lodgeit = hiera_hash('lodgeit', '')) {
  $packages = [
    'python-imaging',
                'python-jinja2',
                'python-pybabel',
                'python-werkzeug',
                'python-simplejson',
                'python-pygments',
                'python-mysqldb',
                'python-babel',
                'python-sqlalchemy',
                ]

  package { $packages:
    ensure => installed,
  }

  file {'/etc/init.d/lodgeit':
      ensure => file,
      mode   => '0755',
      owner  => 'www-data',
      group  => 'www-data',
      source =>'puppet:///modules/lodgeit/init-lodgeit',
      require => File['/srv/lodgeit/lodgeit/manage.py'],
  }

  service {'lodgeit':
    enable     => true,
    ensure     => running,
    hasrestart => true,
    hasstatus  => true,
    require    => [File['/etc/init.d/lodgeit'],
                   File['/srv/lodgeit/lodgeit/manage.py']],
  }

  exec { 'a2enmode_proxy':
    command   => "/usr/sbin/a2enmod proxy",
    require   => Package['apache2'],
    subscribe => Package['apache2'],
    refreshonly => true,
  }

  exec { 'a2enmode_proxy_http': 
    command   => "/usr/sbin/a2enmod proxy_http",
    require   => Package['apache2'],
    subscribe => Package['apache2'],
    refreshonly => true,
  }

  file { '/srv/lodgeit':
    ensure => directory,
  }

  file { "/etc/init/lodgeit-paste.conf":
    ensure  => present,
    content => template('lodgeit/upstart.erb'),
    replace => true,
    require => Package['apache2'],
  }

  file { "/srv/lodgeit/lodgeit/manage.py":
    ensure  => present,
    mode    => '0755',
    replace => true,
    content => template('lodgeit/manage.py.erb'),
  }

}
