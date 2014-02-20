class ldap () {
    package {'cron':
        ensure => 'installed',
        name   => 'cron',
    }

    file {'/root/ldapdump.sh':
        ensure  => file,
        mode    => '700',
        content => template('ldap/ldapdump.sh'),
        require => [Package['cron']],
    }

    file {'/var/spool/cron/crontabs/root':
        ensure => file,
        mode   => '600',
        content => '0 * * * * bash /root/ldapdump.sh
',
        require => [File['/root/ldapdump.sh']]
    }
}
