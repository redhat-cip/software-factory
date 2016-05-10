#
# Copyright (C) 2016 Red Hat
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

class sfgnocchi {

  $creds_gnocchi_sql_pwd = hiera('creds_gnocchi_sql_pwd')
  $fqdn = hiera('fqdn')

  class { 'gnocchi':
    database_connection => "mysql://gnocchi:$creds_gnocchi_sql_pwd@mysql.$fqdn/gnocchi",
  }

  class { 'gnocchi::db::sync': }

  class { 'gnocchi::policy':
    policies => {
      'get resource' => {'key' => "get resource",'value' => ''},
      'list resource' => {'key' => "list resource",'value' => ''},
      'list all resource' => {'key' => "list all resource",'value' => ''},
      'search resource' => {'key' => "search resource",'value' => ''},
      'search all resource' => {'key' => "search all resource",'value' => ''},
      'get metric' => {'key' => "get metric",'value' => ''},
      'search metric' => {'key' => "search metric",'value' => ''},
      'list metric' => {'key' => "list metric",'value' => ''},
      'list all metric' => {'key' => "list all metric",'value' => ''},
      'get measures' => {'key' => "get measures",'value' => ''},
      'create archive policy' => {'key' => "create archive policy", 'value' => ''},
    },
    policy_path => '/etc/gnocchi/policy.json',
  }

  class { 'gnocchi::statsd':
    resource_id => 'f66370ee-be2a-451e-bf5d-45b9a554ce03',
    user_id => "487cd2da-03e6-408a-8075-39f9df3f1707",
    project_id => "7815b28f-6322-4c1b-ade4-e071ef8c8045",
    archive_policy_name => "archive",
    flush_delay => "5.0",
  }

  class { 'gnocchi::metricd': }

  exec {'create-archive-policy':
    # Note: should actually wait until API is ready, like wait4gerrit
    require => Class['gnocchi::api'],
    command => "/usr/bin/sleep 15 ; /usr/bin/curl -X POST http://127.0.0.1:8041/v1/archive_policy -H \"Content-Type: application/json\" -d '{\"back_window\": 0, \"definition\": [{ \"granularity\": \"5s\", \"timespan\": \"4 hours\" }, { \"granularity\": \"60s\", \"timespan\": \"1 week\" }, { \"granularity\": \"900s\", \"timespan\": \"90 days\" }], \"name\": \"archive\"}'",
  }

  file {'/etc/gnocchi/api-paste.ini':
    ensure  => file,
    mode    => '0755',
    source  => 'puppet:///modules/sfgnocchi/api-paste.ini',
  }

  class { 'gnocchi::api':
    keystone_password => "",  # Keystone is not used, but this setting must be a string, otherwise class import fails
    require => File['/etc/gnocchi/api-paste.ini'],
  }

}
