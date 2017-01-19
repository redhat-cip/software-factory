.. _authentication:

Authentication
--------------

Software Factory supports different authentication backend for user.
The `Cauth <http://softwarefactory-project.io/r/gitweb?p=cauth.git;a=shortlog;h=HEAD>`_ component is used to enforce
all authenticated HTTP access.


Admin user
^^^^^^^^^^

The admin user is hard coded and only the password can be defined.
To change the admin user password, edits sfconfig.yaml:

.. code-block:: yaml

  authentication:
    admin_password: userpass



OAuth2-based authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Software Factory allows authentication with several OAuth2-based identity providers. The
following providers are currently supported:

* GitHub
* Google (user data will be fetched from Google+)
* BitBucket

You have to register your SF deployment with the provider of your choice in order to enable
authentication. Please refer to the provider's documentation to do so. The OAuth2 protocol will
always require a callback URL regardless of the provider; this URL is http://fqdn/auth/login/oauth2/callback .

During configuration, the identity provider will generate a client ID and a client secret that are
needed to complete the configuration in sfconfig.yaml. Heres is a example of setting up the GitHub
authentication:

.. code-block:: yaml

 authentication:
   oauth2:
     github:
       disabled: False
       client_id: "Client ID"
       client_secret: "Client Secret"


The other OAuth2 providers can be set up in a similar fashion. Because of possible collisions between
user names and other details, it is advised to use only one provider per deployment.

The GitHub provider also lets you filter users logging in depending on the organizations they belong
to, with the field "github_allowed_organizations". Leave blank if not necessary.


OpenID authentication
^^^^^^^^^^^^^^^^^^^^^

Similarly, an OpenID provider can be used for authentication. Only a single OpenID provider
can be configured at a time, for example to use Launchpad:

.. code-block:: yaml

  authentication:
    openid:
      disabled: False
      server: https://login.launchpad.net/+openid
      login_button_text: "Log in with Launchpad"


OpenID Connect authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An OpenID Connect provider can be used for authentication. Likewise OAuth2, it requires an
application created on the provider to provides a client_id and client_secret. The callback
URL will be: https://fqdn/auth/login/openid_connect/callback .

Moreover it needs an issuer_url to retrieve the openid-configuration. Only a single OpenID
Connect provider can be configured at a time.

.. code-block:: yaml

  authentication:
    openid_connect:
        disabled: False
        issuer_url: https://accounts.google.com/
        login_button_text: "Log in with Google"
        client_id:
        client_secret:

The issuer_url can be tested using the */.well-known/openid-configuration* uri path, e.g.:
https://accounts.google.com/.well-known/openid-configuration

Local user management
^^^^^^^^^^^^^^^^^^^^^

For simple deployments without an Identity Provider, you can manage the users
through the SFManager command-line utility (except for the default admin user, defined
in the sfconfig.yaml file). See SFmanager command-line :ref:`User management <user-management>`
documentation for more details.


Other authentication settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Cookie timeout
""""""""""""""

The SSO cookie timeout can also be changed:

.. code-block:: yaml

  authentication:
    # timeout of sessions in seconds
    sso_cookie_timeout: 43200

Identity provider data sync
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, user data such as full name or email address are synchronized upon each successful login. Users
can disable this behavior in the user settings page (available from top right menu). When disabled, users
can manage the email address used in Software Factory service indepently from the identity provider data.


Redmine API key change
""""""""""""""""""""""

To change the Redmine API key, you need to edit /var/lib/software-factory/bootstrap-data/secrets.yaml and change the value of `redmine_api_key`. Then call `sfconfig.py` to update the key.


Local database access credencials
"""""""""""""""""""""""""""""""""

Each service credencials for mysql database access are stored in /etc/software-factory/sfcreds.yaml.
You can use the `sf_rotate_mysql_passwords.py` command line to replace them all and restart services.
