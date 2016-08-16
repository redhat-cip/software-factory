.. _authentication:

Sofware Factory Authentication
------------------------------

The admin user
^^^^^^^^^^^^^^

Admin user is used to create new repositories, modify ACLs and assign users to projects.


OAuth2-based authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Software Factory allows you to authenticate with several OAuth2-based identity providers. The
following providers are currently supported:

* GitHub
* Google (user data will be fetched from Google+)
* BitBucket

You have to register your SF deployment with the provider of your choice in order to enable
authentication. Please refer to the provider's documentation to do so. The OAuth2 protocol will
always require a callback URL regardless of the provider; this URL is http://yourdomain/auth/login/oauth2/callback .

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


Local user management
^^^^^^^^^^^^^^^^^^^^^

For simple deployments without a Identity Provider,
you can manage the users through the SFManager command-line utility in the :ref:`User Management <sfmanager-user-management>` section.
(except for the default admin user, defined in the sfconfig.yaml file)
can be done through the SFmanager command-line utility :ref:`User management <sfmanager-user-management>`. This backend allows to have
a user database locally.


Admin user password change
^^^^^^^^^^^^^^^^^^^^^^^^^^

To change the admin user password, you need to edit /etc/puppet/hiera/sf/sfconfig.yaml and change the value
of `admin_password`. Then call `sfconfig.sh` to set the password.


Redmine API key change
^^^^^^^^^^^^^^^^^^^^^^

To change the Redmine API key, you need to edit /etc/puppet/hiera/sf/sfcreds.yaml and change the value of
`creds_issues_tracker_api_key`. Then call `sfconfig.sh` to update the key.


Local database access credencials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each service credencials for mysql database access are stored in /etc/puppet/hiera/sf/sfcreds.yaml.
You can use the `sf_rotate_mysql_passwords.py` command line to replace them all and restart services.
