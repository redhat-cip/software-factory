.. _fqdn:

Fully Qualified Domain Name (FQDN)
----------------------------------

The "fqdn" parameter defines the hostname used to access SF services.
It is an important parameter since it is used by external identity provider
to redirect user after authentication. Thus the name needs to be resolvable,
either manually with the /etc/hosts, either with a proper DNS record.

This parameter will be used to create virtual host name for each services,
such as zuul.fqdn and gerrit.fqdn.

.. warning::

    If the *fqdn* parameter is not set, the deployment will use the default
    **sftests.com** domain and users need to set their local /etc/hosts file with:

      ip-of-deployment sftests.com

.. note::

    For consistency, hosts defined in the :ref:`arch inventory<sf-arch>` will
    have their fqdn hostname set to: name.fqdn


Automatic TLS certificate with Let's Encrypt
--------------------------------------------

SF comes with the `lecm <https://github.com/Spredzy/lecm>`_ utility to automatically
manages TLS certificate. To support let's encrypt https security, you need to
enable this option in sfconfig.yaml (and run sfconfig.sh after).

.. code-block:: yaml

  network:
    use_letsencrypt: true


Certificate will be automatically created and renewed, you can check the status using
the *lecm* utility:

.. code-block:: bash

  $ lecm -l
  +----------------------------------+---------------+------------------------------------------------------------------+-----------------------------------------------------------+------+
  |               Item               |     Status    |                          subjectAltName                          |                          Location                         | Days |
  +----------------------------------+---------------+------------------------------------------------------------------+-----------------------------------------------------------+------+
  |   softwarefactory-project.io     |   Generated   |                 DNS:softwarefactory-project.io                   |    /etc/letsencrypt/pem/softwarefactory-project.io.pem    |  89  |
  +----------------------------------+---------------+------------------------------------------------------------------+-----------------------------------------------------------+------+
