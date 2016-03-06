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

class https_cert {

  $gateway_crt = hiera('gateway_crt')

  file {'gateway_cert':
    ensure  => file,
    path    => '/etc/pki/ca-trust/source/anchors/gateway.crt',
    content => inline_template('<%= @gateway_crt %>'),
    mode    => '0644',
  }

  exec {'update-ca-trust':
    command => 'update-ca-trust',
    path    => '/usr/bin/:/bin/:/usr/local/bin',
    require => File['gateway_cert'],
  }

  # python-requests doesn't use the systems CA database, thus replacing it's own
  # CA list with SF certificate CA
  exec {'cacert.pem':
    path    => '/usr/bin/:/bin/:/usr/local/bin',
    command => 'cp /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt /usr/lib/python2.7/site-packages/requests/cacert.pem',
    require => File['gateway_cert'],
  }
}
