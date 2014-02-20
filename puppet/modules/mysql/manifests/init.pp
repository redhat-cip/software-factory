class mysql () {
    package {'cron':
        ensure => 'installed',
        name   => 'cron',
    }

    file {'/root/mysqldump.sh':
        ensure  => file,
        mode    => '700',
        content => template('mysql/mysqldump.sh'),
        require => [Package['cron']],
    }

    file {'/var/spool/cron/crontabs/root':
        ensure => file,
        mode   => '600',
        content => '0 * * * * bash /root/mysqldump.sh\n',
        require => [File['/root/mysqldump.sh']]
    }
}
