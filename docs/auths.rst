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

For simple deployments without a LDAP backend for users or github authentication,
user management (except for the default admin user, defined in the sfconfig.yaml file)
can be done through the SFmanager command-line utility.

This backend allow to have a little user database locally.
