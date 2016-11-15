.. _gerritlinks-user:

Gerrit comments link customisation
==================================

You can configure how gerrit render link from commit message
using the config-repository gerrit/commentlinks.yaml file:

* git clone the config-repository
* edit the gerrit/commentlinks.yaml, for example adding bugzilla.redhat.com:

.. code-block:: yaml

   commentlinks:
     - name: External_Bugzilla_addressing
       match: "BZ:\\s+#?(\\d+)"
       html: "BZ: <a href=\"https://bugzilla.redhat.com/show_bug.cgi?id=$2\">$2</a>"

* submit and merge the config change.

Note that this is just for automatic link rendering in gerrit web interface.
To actually update the issue, a hook manager (to be developped) is required
in managesf service.
