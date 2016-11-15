.. _resources-operator:

Managing resources via the config repository
============================================

Fetch missing resources from services to the config repository
--------------------------------------------------------------

See this introduction about this feature :ref:`here <resources-user>`

When resources are created outside of the config/resources tree then
*resources.sh* can be used to synchronize the resources tree.

The *get_missing_resources* mode of *resources.sh* inspect services
to find resources that are not defined in the config/resources tree and
it will propose via Gerrit a change that need to be approved to re-sync the
config/resources tree.

.. code-block:: bash

   /usr/local/bin/resources.sh get_missing_resources submit

Note the commit message of the proposed change on Gerrit contains
the flag "sf-resources: skip-apply" that tell the config-update job
to skip the apply of the proposed resources. They are just merged
in the config/resources tree as they already exist on services.

Prevent usage of legacy endpoints
---------------------------------

If you choose to use this workflow to manage resources via the config
repository in place of the legacy endpoint then it is safe to be sure
the platform policies does not allow access for users other than the admin
to the projects, memberships and groups endpoints. You should refer to this
:ref:`section <access_control>` to verify the policies and take the
required actions.
