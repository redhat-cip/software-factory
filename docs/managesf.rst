
Contents:

.. toctree::

Managing Software factory
=========================

This page describes about the ways to manage softwarefactory

.. _managesf_create_project:

Create Project
--------------

Softwarefacty exposes ways to create and initialize projects in redmine
and gerrit simultaneously. Initializing a project involves setting up the
ACL and initializing the source repository.

SoftwareFactory allows you to create projects in one of the following ways.

- REST API

  *PUT /project/{project-name}*

  In the request body additional data can be provided as CreateProjectInput_

  Request
  ::

      PUT /project/test-project
      Content-Type: application/json;charset=UTF-8
      Cookie: auth_pubtkt=..

      {
        "description": "This is a test project",
        "core-group-members": ["user1", "user2"],
        "ptl-group-members": ["user3"],
        "dev-group-members": ["user1", "user2", "user3"],
        "upstream": "http://github.com/enovance/SoftwareFactory",
        "private": true
      }

  Response

  If successfully created, HTTP status code 200 is returned


- CLI

  sf-manage create --help will yield the necessary infromation to
  create a project


Delete Project
--------------

Softwarefacty exposes ways to delete projects and the groups
associated with the project in redmine and gerrit simultaneously.

For any project, only the PTLs shall have the permission to delete it.

SoftwareFactory allows you to delete projects in one of the following ways.

- REST API

  *DELETE /project/{project-name}*

  Request
  ::

    DELETE /project/test-project
    Cookie: auth_pubtkt=..

  Response:

  If successfully deleted, HTTP status code 200 is returned
  In case of errors, appropriate message will be sent with the response

- CLI

  sf-manage delete --help will yield the necessary infromation to
  delete a project

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
