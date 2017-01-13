.. _access_control:

Access control
==============

Software Factory comes with a policy engine allowing an operator to control who
can do what on the managesf REST API.

The config repository includes the policy definition file (policy.yaml) that
shows the default policies on Software Factory. Modifying these rules will
override the default behavior.

How to change access policies
-----------------------------

* git clone the config-repository
* edit the config/policies/policy.yaml file to suit your needs
* submit the config change
* have the change reviewed and approved by an operator
* the policies will be updated after the change is automatically merged, once
  the config-update job has run its course.

Writing custom rules
--------------------

The policy engine is based on OpenStack's oslo.policy. You can therefore refer
to the documentation of this project for further information: http://docs.openstack.org/developer/oslo.policy/

The rules are defined as such:

.. code-block:: yaml

  "rule_name": "rule_description"

where rule_description is a boolean combination of one or more fundamental blocks.
Fundamental blocks can have the following form:

.. code-block:: yaml

  "rule:rule_name"

to refer to a previously created rule or

.. code-block:: yaml

  "property:value"

where **property** is a property of the user requesting the action (for example
*username*, *group*, or *is_authenticated*) and **value** a hard-coded value (for
example *True* or *user3*) or the value of the target property (for example *%(username)s*
or *%(project)s*).

The following user properties are supported:

* **username**: the username of the requesting user on Software Factory
* **group**: the groups the requesting user belongs to. The rule 'group:A' will
  match if A is one of the groups the user belongs to.
* **is_authenticated**: will match to True if the user is logged in.

The following target values are supported:

* **%(username)s**: the username of the user on which the action would apply (if relevant)
* **%(project)s**: the project on which the action would apply (if relevant)
* **target.group**: the group targeted by the action (if relevant, typically for membership operations)
* **%(group)s**: the group targeted by the action when checking that the user belongs to this group

Default rules
-------------

The following default rules are set for convenience. They can be overridden if
necessary, or reused to extend other rules.

* **admin_or_service**: allow the admin user or the SF service user only
* **admin_api**: allow the admin user only
* **is_owner**: allow the user himself/herself only (applies to user-related API operations only)
* **admin_or_owner**: allow the user owning the resource or the admin only (applies to user-related API operations only)
* **ptl_api**: allow PTL users of this project only (applies to project-related API operations only)
* **core_api**: allow core users of this project only (applies to project-related API operations only)
* **dev_api**: allow dev users of this project only (applies to project-related API operations only)
* **contributor_api**: allow PTL, core or dev users of this project only (applies to project-related API operations only)
* **authenticated_api**: allow any logged in user
* **any**: allow anybody
* **none**: allow nobody

Examples
--------

Allow admin or user Bob to create projects
..........................................

.. code-block:: yaml

  'managesf.project:create': 'rule:admin_api or user:Bob'

Check if the targeted group of the action is the targeted project's dev group
.............................................................................

.. code-block:: yaml

  'my_rule': 'target.group:%(project)s-dev'

Allow users that belong to the targeted group
.............................................

.. code-block:: yaml

  'my_other_rule': 'group:%(group)s'
