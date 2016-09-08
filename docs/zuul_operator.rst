Configure zuul
--------------

Software Factory only allows adding gerrit connections to Zuul,
the rest of the configuration is set for correct integration with
the rest of SF services.


Third-party CI configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can configure Zuul to connect to a remote gerrit event stream.
First you need a Non-Interactive Users created on the external gerrit.
Then you need to configure that user to use the local zuul ssh public key:
/var/lib/zuul/.ssh/id_rsa.pub
Finally you need to activate the gerrit_connections setting in sfconfig.yaml:

.. code-block:: yaml

   gerrit_connections:
        - name: openstack_gerrit
          hostname: review.openstack.org
          puburl: https://review.openstack.org/r/
          username: third-party-ci-username


To benefit from Software Factory CI capabilities as a third party CI, you
also need to configure the config repository to enable a new gerrit trigger.
For example, to setup a basic check pipeline, add a new 'zuul/thirdparty.yaml'
file like this:

.. code-block:: yaml

    pipelines:
        - name: 3rd-party-check
          manager: IndependentPipelineManager
          source: openstack_gerrit
          trigger:
              openstack_gerrit:
                  - event: patchset-created


Notice the source and trigger are called 'openstack_gerrit' as set in the
gerrit_connection name, instead of the default 'gerrit' name.

See the :ref:`Zuul user documentation<zuul-user>` for more details.
