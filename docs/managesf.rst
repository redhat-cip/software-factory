.. toctree::

Managing Software factory
=========================

This page describes the ways to manage Software Factory

.. _managesf_create_project:

Create Project
--------------

SF exposes ways to create and initialize projects in Redmine
and Gerrit simultaneously. Initializing a project involves setting up the
ACL and initializing the source repository.

Any user that can authenticate against SF will be able to create a project.

SF allows you to create projects in one of the following ways.

REST API call
'''''''''''''

.. code-block:: none

 *PUT /project/{project-name}*

In the request body additional data can be provided as CreateProjectInput_

Request

.. code-block:: guess

 PUT /project/test-project
 Content-Type: application/json;charset=UTF-8
 Cookie: auth_pubtkt=..

 {
  "description": "This is a test project",
  "core-group-members": ["user1", "user2"],
  "ptl-group-members": ["user3"],
  "dev-group-members": ["user1", "user2", "user3"],
  "upstream": "http://github.com/enovance/software-factory",
  "private": true
 }

Response

If successfully created, HTTP status code 200 is returned

CLI
'''
.. code-block:: bash

 $ sf-manage --host <sfgateway.dom> --auth-server <sfgateway.dom> --auth user:password create --name <project-name>

You can use the argument '-h' to the create action to display create options.


Delete Project
--------------

SF exposes ways to delete projects and the groups associated with the project
in Redmine and Gerrit simultaneously.

For any project, only the PTLs shall have the permission to delete it.

SF allows you to delete projects in one of the following ways.

REST API Call
'''''''''''''
.. code-block:: none

 *DELETE /project/{project-name}*

Request

.. code-block:: guess

 DELETE /project/test-project
 Cookie: auth_pubtkt=..

Response

If successfully deleted, HTTP status code 200 is returned
In case of errors, appropriate message will be sent with the response

CLI
'''
.. code-block:: bash

 $ sf-manage --host <sfgateway.dom> --auth-server <sfgateway.dom> --auth user:password delete --name <project-name>


Add user to project groups
--------------------------

SF exposes ways to add user to specified groups associated to a project in Redmine and
Gerrit simultaneously.

If the caller user is in the PTL group of the project then the user can add user in
any groups.

If the caller user is in the core user groups of the project then the user can:

 - Add user to the core group
 - Add user to the dev group

If the caller user is in the dev user groups or even not in any groups related to that project
then the user cannot add users in any groups.

SF allows you to add user in groups in one of the following way.

REST API Call
'''''''''''''
.. code-block:: none

 *PUT /project/membership/{project-name}/{user-name}*

In the request body additional data can be provided as AddUserToProjectInput_

Request

.. code-block:: guess

 PUT /project/membership/p1/user1
 Content-Type: application/json;charset=UTF-8
 Cookie: auth_pubtkt=..

 {
  "groups": ["p1-ptl", "p1-core"],
 }

Response

If successfully created, HTTP status code 200 is returned

CLI
'''
.. code-block:: bash

 $ sf-manage --host <sfgateway.dom> --auth-server <sfgateway.dom> --auth user:password add_user --name user1 --groups p1-ptl,p1-core

You can use the argument '-h' to the create action to display create options.


Remove user from project groups
-------------------------------

SF exposes ways to remove user from specified or all groups associated to a project in Redmine and
Gerrit simultaneously.

If the caller user is in the PTL group of the project then the user can remove user in
any groups.

If the caller user is in the core user groups of the project then the user can:

 - Remove user to the core group
 - Remove user to the dev group

If the caller user is in the dev user groups or even not in any groups related to that project
then the user cannot remove users in any groups.

If the request does not provide a specific group to delete the user from, SF will
remove the user from all group associated to a project.

SF allows you to remove a user from groups in one of the following way.

REST API Call
'''''''''''''
.. code-block:: none

 *DELETE /project/membership/{project-name}/{user-name}/{group-name}*
 *DELETE /project/membership/{project-name}/{user-name}*

In the request body additional data can be provided as AddUserToProjectInput_

Request

.. code-block:: guess

 DELETE /project/membership/p1/user1/p1-core
 Cookie: auth_pubtkt=..

Response

If successfully created, HTTP status code 200 is returned

CLI
'''
.. code-block:: bash

 $ sf-manage --host <sfgateway.dom> --auth-server <sfgateway.dom> --auth user:password delete_user --name user1 --group p1-ptl
 $ sf-manage --host <sfgateway.dom> --auth-server <sfgateway.dom> --auth user:password delete_user --name user1

You can use the argument '-h' to the create action to display create options.


Setup remote replication for a project
--------------------------------------

 # To be filled

Create SF backup
----------------

SF exposes ways to perform and retrieve a backup of all the user data store in your
SF installation. This backup can be used in case of disaster to quickly
recover user data on the same or other SF installation (in the same version).

Only the SF administrator can perform and retrieve a backup.

SF allows you to perform a backup in one of the following way.

REST API Call
'''''''''''''
.. code-block:: none

 *GET /backup*

Request

.. code-block:: guess

 GET /backup
 Cookie: auth_pubtkt=..

Response

If successfully created, HTTP status code 200 is returned and
the body contains a gzip tar archive.

.. _CreateBackupCli:

CLI
'''

.. code-block:: bash

 $ sf-manage --host <sfgateway.dom> --auth-server <sfgateway.dom> --auth user:password backup_get

A file called "sf_backup.tar.gz" will be create in the local directory.


Restore a backup
----------------

SF exposes ways to restore a backup of all the user data store in your
SF installation. This backup can be used in case of disaster to quickly
recover user data on the same or other SF installation (in the same version).

Only the SF administrator can restore a backup.

SF allows you to restore a backup in one of the following way.

REST API Call
'''''''''''''

.. code-block:: none

 *POST /restore*

The backup archive must be copied in the request body as multipart form data.

Request

.. code-block:: guess

 POST /backup
 Content-Type: Content-Type: multipart/form-data; boundary=...
 Content-Length: ...
 Cookie: auth_pubtkt=..

Response

If successfully restored, HTTP status code 200 is returned. It may
take sometime for SF REST API to return an HTTP response.


CLI
'''

.. code-block:: bash

 $ sf-manage --host <sfgateway.dom> --auth-server <sfgateway.dom> --auth user:password restore --filename sf_backup.tar.gz

.. _CreateProjectInput:

CreateProjectInput
------------------

===================  ==========  ===============================
     Field Name                      Description
===================  ==========  ===============================
description           Optional    A brief description about the
                                  project
core-group-members    Optional    The core developers for the
                                  projects separated by comma (,)
ptl-group-members     Optional    The project team leaders
                                  separated by comma (,)
dev-group-members     Optional    Developers for the project
                                  separated by comma (,)
upstream              Optional    Link to a git repo from which
                                  the current project's repo is
                                  initialized
private               Optional    If set true, the project will
                                  be not be visible to users who
                                  are not in core-group,
                                  ptl-group and dev-group. If not
                                  true, the project would be
                                  visible to all the users
===================  ==========  ===============================

.. _AddUserToProjectInput:

AddUserToProjectInput
---------------------

===================  ==========  ===============================
     Field Name                      Description
===================  ==========  ===============================
groups                Mandatory   A list of group to add user
===================  ==========  ===============================
