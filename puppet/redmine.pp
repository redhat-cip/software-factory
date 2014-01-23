class redmine {

  package {redmine:
    name => $operatingsystem ? {
      debian  => 'redmine',
      ubuntu  => 'redmine'
    },
    ensure => 'installed'
  }

  package {apache2:
    name => $operatingsystem ? {
      debian  => 'apache2',
      ubuntu  => 'apache2'
    },
    ensure => 'installed'
  }

  package {libapache2-mod-passenger:
    name => $operatingsystem ? {
      debian  => 'libapache2-mod-passenger',
      ubuntu  => 'libapache2-mod-passenger'
    },
    ensure => 'installed'
  }

  service {apache2:
    ensure => running,
    require => [Package['apache2'], Package['libapache2-mod-passenger']],
  }

  file {'/etc/redmine/default/database.yml':
  	ensure  => file,
    	mode => 0640,
	owner => "www-data",
	group => "www-data",
  	content => template('redmine/database.erb'),
  }

  file {'/etc/apache2/mods-available/passenger.conf':
  	ensure  => file,
    	mode => 0640,
	owner => "www-data",
	group => "www-data",
    	source =>'puppet:///modules/redmine/passenger.conf',
	notify => Service[apache2],
  }

  file {'/etc/apache2/sites-available/redmine':
  	ensure  => file,
    	mode => 0640,
	owner => "www-data",
	group => "www-data",
    	source =>'puppet:///modules/redmine/redmine',
	notify => Service[apache2],
  }

  file { "/etc/apache2/sites-enabled/000-default":
    	ensure  => absent,
  }

  exec {"enable_redmine_site":
	command => "a2ensite redmine",
	path    => "/usr/sbin/:/usr/bin/:/bin/",
	require => [File['/etc/apache2/sites-available/redmine']],
  }

  exec {"create_session_store":
	command => "rake generate_session_store",
	path    => "/usr/bin/:/bin/",
	cwd     => '/usr/share/redmine', 
	require => [File['/etc/redmine/default/database.yml']],
  }

  exec {"create_db":
	environment => ["RAILS_ENV=production"],
	command => "rake db:migrate --trace",
	path    => "/usr/bin/:/bin/",
	cwd     => '/usr/share/redmine', 
	require => [Exec['create_session_store']],
  }

  exec {"default_data":
	environment => ["RAILS_ENV=production", "REDMINE_LANG=en"],
	command => "rake redmine:load_default_data --trace",
	path    => "/usr/bin/:/bin/",
	cwd     => '/usr/share/redmine',
	require => [Exec['create_db']],
  }


}
