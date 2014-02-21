class ssmtp ($settings = hiera_hash('ssmtp', '')) {
    package {'ssmtp':
        ensure => 'installed',
        name   => 'ssmtp',
    }

    file {'/etc/ssmtp/ssmtp.conf':
        ensure  => file,
        mode    => '644',
        content => template('ssmtp/ssmtp.conf'),
        require => [Package['ssmtp']],
    }
}
