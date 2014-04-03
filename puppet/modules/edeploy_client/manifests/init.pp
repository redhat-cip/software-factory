#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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
