class redmine ($settings = hiera_hash('redmine', '')) {
    package {'redmine':
        ensure => 'installed',
        name   => 'redmine',
    }

    package {'apache2':
        ensure => 'installed',
        name   => 'apache2',
    }

    package {'libapache2-mod-passenger':
        ensure => 'installed',
        name   => 'libapache2-mod-passenger',
    }

    service {'apache2':
        ensure  => running,
        require => [Package['apache2'], Package['libapache2-mod-passenger']],
    }

    file {'/etc/redmine/default/database.yml':
        ensure  => file,
        mode    => '0640',
        owner   => 'www-data',
        group   => 'www-data',
        content => template('redmine/database.erb'),
    }

    file {'/etc/apache2/mods-available/passenger.conf':
        ensure => file,
        mode   => '0640',
        owner  => 'www-data',
        group  => 'www-data',
        source =>'puppet:///modules/redmine/passenger.conf',
        notify => Service[apache2],
    }

    file {'/etc/apache2/sites-available/redmine':
        ensure => file,
        mode   => '0640',
        owner  => 'www-data',
        group  => 'www-data',
        source =>'puppet:///modules/redmine/redmine',
        notify => Service[apache2],
    }

    file { '/etc/apache2/sites-enabled/000-default':
        ensure => absent,
    }
  
    file { '/root/activate-api-for-admin.sql':
        ensure  => present,
        mode    => '0640',
        content => template('redmine/activate-api-for-admin.sql.erb'),
        replace => true,
    }

    exec {'enable_redmine_site':
        command => 'a2ensite redmine',
        path    => '/usr/sbin/:/usr/bin/:/bin/',
        require => [File['/etc/apache2/sites-available/redmine']],
    }

    exec {'create_session_store':
        command => 'rake generate_session_store',
        path    => '/usr/bin/:/bin/',
        cwd     => '/usr/share/redmine',
        require => [File['/etc/redmine/default/database.yml']],
    }

    exec {'create_db':
        environment => ['RAILS_ENV=production'],
        command     => 'rake db:migrate --trace',
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/share/redmine',
        require     => [Exec['create_session_store']],
    }

    exec {'default_data':
        environment => ['RAILS_ENV=production', 'REDMINE_LANG=en'],
        command     => 'rake redmine:load_default_data --trace',
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/share/redmine',
        require     => [Exec['create_db']],
    }

    exec {'ldap_auth':
        environment => ['RAILS_ENV=production', 'REDMINE_LANG=en'],
        command     => 'mysql -u redmine redmine -psecret -h sf-mysql < /root/redmine_ldap.sql',
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/bin',
        require     => [Exec['default_data']],
    }
    
    exec {'init_api_key':
        command     => 'mysql -u redmine redmine -psecret -h sf-mysql < /root/activate-api-for-admin.sql',
        path        => '/usr/bin/:/bin/',
        cwd         => '/usr/bin',
        require     => [Exec['ldap_auth']],
    }
}
