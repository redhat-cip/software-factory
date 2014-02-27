class edeploy_client {
  exec {'set edeploy server address':
    command  => "/bin/sed -i \"s/^RSERV=.*//\" conf; sed -i \"/^$/d\" conf; /bin/echo \"RSERV=sf-edeploy-server\" >> conf",
    cwd      => '/var/lib/edeploy',
  }
  exec {'set edeploy server address port':
    command  => "/bin/sed -i \"s/^RSERV_PORT=.*//\" conf; sed -i \"/^$/d\" conf; /bin/echo \"RSERV_PORT=873\" >> conf",
    cwd      => '/var/lib/edeploy',
  }
}
