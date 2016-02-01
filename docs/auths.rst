.. toctree::

Sofware Factory Authentication
==============================

The admin user
--------------

Admin user is used to create new repositories, modify ACLs and assign users to projects.

Github authentication
---------------------

You have to register your SF deployment in Github to enable Github
authentication.

#. Login to your Github account, go to Settings -> Applications -> "Register new application"
#. Fill in the details and be careful when setting the authorization URL. It will look
   like this: http://yourdomain/auth/login/github/callback
#. Set the corresponding values in bootstrap/sfconfig.yaml:

.. code-block:: none

 github_app_id: "Client ID"
 github_app_secret: "Client Secret"
 github_allowed_organization: comma-separated list of organizations that are allowed to access this SF deployment.

Note that a user has to be member of at least one of this organizations to use this SF deployment.
Leave empty if not required.

Local user management
---------------------

For simple deployments without a LDAP backend or Github authentication,
you can manage the users through the SFManager command-line utility in the `User Management` section.
(except for the default admin user, defined in the sfconfig.yaml file)
can be done through the SFmanager command-line utility `User management`. This backend allows to have
a user database locally.


Admin user password change
--------------------------

To change the admin user password, you need to edit /etc/puppet/hiera/sf/sfconfig.yaml and change the value
of `admin_password`. Then call `sfconfig.sh` to set the password.


Redmine API key change
----------------------

To change the Redmine API key, you need to edit /etc/puppet/hiera/sf/sfcreds.yaml and change the value of
`creds_issues_tracker_api_key`. Then call `sfconfig.sh` to update the key.


Github Secret change
--------------------

To change the Github App Secret, you need to login to your Github account, got to Settings -> Applications ->
"Reset client secret". Then update /etc/puppet/hiera/sf/sfconfig.yaml and call `sfconfig.sh`.


Local database access credencials
---------------------------------

Each service credencials for mysql database access are stored in /etc/puppet/hiera/sf/sfcreds.yaml.
You can use the `sf_rotate_mysql_passwords.py` command line to replace them all and restart services.
